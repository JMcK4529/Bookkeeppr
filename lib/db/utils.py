import logging
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


def get_app_data_folder_path() -> Path:
    """Return the full path to the Bookkeeppr app data folder, platform-aware."""
    system = platform.system()
    if system == "Windows":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        return Path(base) / "Bookkeeppr"
    else:
        return Path.home() / ".Bookkeeppr"


def get_db_path() -> Path:
    """Return the full path to the Bookkeeppr database, platform-aware."""
    return get_app_data_folder_path() / ".bookkeeppr.db"


def get_recovery_path() -> Path:
    """Return the full path to the database recovery folder, platform-aware."""
    return get_app_data_folder_path() / "recovery"


def database_exists() -> bool:
    """Check if the database file exists at the platform-specific location."""
    db_path = get_db_path()
    exists = db_path.exists()
    logger.info(
        f"[DB] Looking for DB at {db_path}... {'Found' if exists else 'Not found'}"
    )
    return exists


def get_schema_path() -> Path:
    """
    Returns the path of the schema.sql, whether in frozen mode or not
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS) / "lib" / "db" / "sql"
    else:
        base_path = Path(__file__).parent

    schema_path = base_path / "schema.sql"

    if not schema_path.exists():
        logger.error(f"[DB] Schema file not found at {schema_path}")
        raise FileNotFoundError(f"Schema not found at {schema_path}")

    return schema_path


def init_db() -> None:
    db_path = get_db_path()
    if db_path.exists():
        logger.info(f"[DB] Database already exists at {db_path}")
        return

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure recovery directory exists
    get_recovery_path().mkdir(parents=True, exist_ok=True)

    # Connect and initialize schema
    conn = sqlite3.connect(db_path)
    schema_path = get_schema_path()

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)

    conn.commit()
    conn.close()
    logger.info(f"[DB] Initialized new database at {db_path}")


# --- Recovery DB utility ---
def create_recovery_db() -> Path:
    """Create a recovery SQLite DB."""
    recovery_dir = get_recovery_path()
    recovery_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    recovery_path = recovery_dir / f"{timestamp}.db"

    # Create empty DB
    schema_path = get_schema_path()
    conn = sqlite3.connect(recovery_path)
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)

    return recovery_path


def backup_deleted_entity(entity, repo_class) -> None:
    """Populate a recovery database with an entity and its related transactions."""
    try:
        recovery_db_path = create_recovery_db()
        recovery_repo = repo_class(db_path=recovery_db_path)
        recovery_repo.create(entity)
        transactions_repo = recovery_repo.transaction_repository(
            db_path=recovery_db_path
        )
        transactions = recovery_repo.get_transactions(entity)
        for transaction in transactions:
            transactions_repo.create(transaction)
        logger.info(
            "[RECOVERY] Successfully backed up entity and transactions."
        )
    except Exception as err:
        logger.error(f"[RECOVERY] Recovery failed due to error:\n{err}")
        raise

    return


def backup_deleted_transactions(transactions, repo_class) -> None:
    """Populate a recovery database with an entity and its related transactions."""
    try:
        recovery_db_path = create_recovery_db()
        recovery_repo = repo_class(db_path=recovery_db_path)
        for transaction in transactions:
            recovery_repo.create(transaction)

        logger.info("[RECOVERY] Successfully backed up transaction(s).")
    except Exception as err:
        logger.error(f"[RECOVERY] Recovery failed due to error:\n{err}")
        raise

    return


def delete_old_recovery_dbs(older_than_days: int = 30) -> None:
    """Delete recovery database files older than a given number of days."""
    recovery_dir = get_recovery_path()
    if not recovery_dir.exists():
        logger.warning("[CLEANUP] Recovery directory does not exist.")
        return

    cutoff = datetime.now().timestamp() - (older_than_days * 86400)
    deleted_files = 0

    for db_file in recovery_dir.glob("*.db"):
        try:
            # Check if filename matches the expected pattern: YYYYMMDD_HHMMSS.db
            if db_file.stem.count("_") != 1:
                continue
            datetime.strptime(db_file.stem, "%Y%m%d_%H%M%S")  # Validate format

            if db_file.stat().st_mtime < cutoff:
                db_file.unlink()
                deleted_files += 1
                logger.info(
                    f"[CLEANUP] Deleted old recovery DB: {db_file.name}"
                )
        except Exception as e:
            logger.warning(f"[CLEANUP] Skipped {db_file.name}: {e}")

    logger.info(f"[CLEANUP] Deleted {deleted_files} old recovery database(s).")


def normalize_datetime(dt_str, output_format="%Y-%m-%d %H:%M:%S"):
    """Try to parse a datetime string using multiple possible formats.

    Returns a string formatted to `output_format` or None if no match found.
    """
    if not dt_str:
        return None

    formats = [
        "%Y-%m-%dT%H:%M",  # HTML datetime-local input
        "%Y-%m-%d %H:%M",  # space-separated
        "%Y-%m-%dT%H:%M:%S",  # T-separated with seconds
        "%Y-%m-%d %H:%M:%S",  # space-separated with seconds
        "%Y-%m-%d",  # just the date
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.strftime(output_format)
        except ValueError:
            continue

    return None

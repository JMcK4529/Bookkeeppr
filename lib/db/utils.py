import os
import platform
from pathlib import Path
import sqlite3
from customer import Customer, CustomerRepository
from purchase import Purchase, PurchaseRepository
from sale import Sale, SaleRepository
from supplier import Supplier, SupplierRepository


def get_db_path() -> Path:
    """Return the full path to the Bookkeeppr database, platform-aware."""
    system = platform.system()
    if system == "Windows":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        return Path(base) / "Bookkeeppr" / "bookkeeppr.db"
    else:
        return Path.home() / ".bookkeeppr.db"


def database_exists() -> bool:
    """Check if the database file exists at the platform-specific location."""
    db_path = get_db_path()
    exists = db_path.exists()
    print(
        f"[DB] Looking for DB at {db_path}... {'Found' if exists else 'Not found'}"
    )
    return exists


def init_db() -> None:
    db_path = get_db_path()
    if db_path.exists():
        print(f"[DB] Database already exists at {db_path}")
        return

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect and initialize schema
    conn = sqlite3.connect(db_path)
    schema_path = Path(__file__).parent / "schema.sql"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)

    conn.commit()
    conn.close()
    print(f"[DB] Initialized new database at {db_path}")

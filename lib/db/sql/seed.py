from typing import Optional
from lib.db.utils import *


def run_sql_script(path: str, db_path: Optional[Path] = None) -> None:
    db_path = db_path or get_db_path()
    with sqlite3.connect(db_path) as conn:
        with open(path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()


def refresh_tables() -> None:
    run_sql_script("lib/db/sql/drop_tables.sql")
    run_sql_script("lib/db/schema.sql")


def seed() -> None:
    run_sql_script("lib/db/sql/seed.sql")


def big_seed() -> None:
    run_sql_script("lib/db/sql/big_seed_purchases.sql")
    run_sql_script("lib/db/sql/big_seed_sales.sql")


def cleanup() -> None:
    run_sql_script("lib/db/sql/cleanup.sql")

import logging
import sqlite3
from pathlib import Path
from typing import Optional, List
from lib.db.entity import Entity, EntityRepository
from lib.db.purchase import Purchase, PurchaseRepository
from lib.db.utils import get_db_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Supplier(Entity):
    def __init__(self, id: Optional[int], name: str) -> None:
        self.id = id
        self.name = name

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Supplier)
            and self.id == other.id
            and self.name == other.name
        )

    def __repr__(self):
        return f"Supplier(id={self.id}, name='{self.name}')"


class SupplierRepository(EntityRepository[Supplier]):
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def create(self, supplier: Supplier) -> Supplier:
        created_supplier = None
        with self._connect() as conn:
            cursor = conn.cursor()
            if supplier.id is None:
                cursor.execute(
                    "INSERT INTO suppliers (name) VALUES (?)", (supplier.name,)
                )
                conn.commit()
                created_supplier = Supplier(cursor.lastrowid, supplier.name)
            else:
                cursor.execute(
                    "INSERT INTO suppliers (id, name) VALUES (?, ?)",
                    (supplier.id, supplier.name),
                )
                conn.commit()
                created_supplier = supplier
            return created_supplier

    def read(
        self, id: Optional[int] = None, name: Optional[str] = None
    ) -> Optional[Supplier]:
        with self._connect() as conn:
            cursor = conn.cursor()
            if id is not None:
                cursor.execute(
                    "SELECT id, name FROM suppliers WHERE id = ?", (id,)
                )
            elif name is not None:
                cursor.execute(
                    "SELECT id, name FROM suppliers WHERE name = ?", (name,)
                )
            else:
                raise ValueError(
                    "Either id or name required to read a supplier"
                )

            row = cursor.fetchone()
            return Supplier(*row) if row else None

    def update(self, supplier: Supplier) -> Supplier:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE suppliers SET name = ? WHERE id = ?",
                (supplier.name, supplier.id),
            )
            cursor.execute(
                "UPDATE purchases SET supplier_name = ? WHERE supplier_id = ?",
                (supplier.name, supplier.id),
            )
            conn.commit()
            return self.read(id=supplier.id)

    def delete(self, id: int) -> Optional[Supplier]:
        supplier = self.read(id=id)
        if not supplier:
            return None
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (id,))
            # Propagate deletion to purchases
            cursor.execute(
                "DELETE FROM purchases WHERE supplier_id = ?", (id,)
            )
            conn.commit()
            return supplier

    def search(self, name_query: str) -> List[Supplier]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM suppliers WHERE LOWER(name) LIKE ?",
                (f"%{name_query.lower()}%",),
            )
            rows = cursor.fetchall()
            return [Supplier(id=row[0], name=row[1]) for row in rows]

    def all(self) -> list[Supplier]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM suppliers",
            )
            rows = cursor.fetchall()
            return [Supplier(id=row[0], name=row[1]) for row in rows]

    def transaction_repository(
        self, db_path: Optional[Path] = None
    ) -> PurchaseRepository:
        repo = PurchaseRepository(db_path)
        return repo

    def get_transactions(self, supplier: Supplier) -> List[Purchase]:
        repo = self.transaction_repository()
        transactions = repo.search_by_parent(supplier)
        return transactions

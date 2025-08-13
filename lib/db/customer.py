import logging
import sqlite3
from pathlib import Path
from typing import Optional, List
from lib.db.entity import Entity, EntityRepository
from lib.db.sale import Sale, SaleRepository
from lib.db.utils import get_db_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Customer(Entity):
    def __init__(self, id: Optional[int], name: str) -> None:
        self.id = id
        self.name = name

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Customer)
            and self.id == other.id
            and self.name == other.name
        )

    def __repr__(self):
        return f"Customer(id={self.id}, name='{self.name}')"


class CustomerRepository(EntityRepository[Customer]):
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def create(self, customer: Customer) -> Customer:
        created_customer = None
        with self._connect() as conn:
            cursor = conn.cursor()
            if customer.id is None:
                cursor.execute(
                    "INSERT INTO customers (name) VALUES (?)", (customer.name,)
                )
                conn.commit()
                created_customer = Customer(cursor.lastrowid, customer.name)
            else:
                cursor.execute(
                    "INSERT INTO customers (id, name) VALUES (?, ?)",
                    (customer.id, customer.name),
                )
                conn.commit()
                created_customer = customer
            return created_customer

    def read(
        self, id: Optional[int] = None, name: Optional[str] = None
    ) -> Optional[Customer]:
        with self._connect() as conn:
            cursor = conn.cursor()
            if id is not None:
                cursor.execute(
                    "SELECT id, name FROM customers WHERE id = ?", (id,)
                )
            elif name is not None:
                cursor.execute(
                    "SELECT id, name FROM customers WHERE name = ?", (name,)
                )
            else:
                raise ValueError(
                    "Either id or name required to read a customer"
                )

            row = cursor.fetchone()
            return Customer(*row) if row else None

    def update(self, customer: Customer) -> Customer:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET name = ? WHERE id = ?",
                (customer.name, customer.id),
            )
            # Propagate change to sales
            cursor.execute(
                "UPDATE sales SET customer_name = ? WHERE customer_id = ?",
                (customer.name, customer.id),
            )
            conn.commit()
            return self.read(id=customer.id)

    def delete(self, id: int) -> Optional[Customer]:
        customer = self.read(id=id)
        if not customer:
            return None
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers WHERE id = ?", (id,))
            # Propagate deletion to sales
            cursor.execute("DELETE FROM sales WHERE customer_id = ?", (id,))
            conn.commit()
            return customer

    def search(self, name_query: str) -> List[Customer]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM customers WHERE LOWER(name) LIKE ?",
                (f"%{name_query.lower()}%",),
            )
            rows = cursor.fetchall()
            return [Customer(id=row[0], name=row[1]) for row in rows]

    def all(self) -> List[Customer]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM customers",
            )
            rows = cursor.fetchall()
            return [Customer(id=row[0], name=row[1]) for row in rows]

    def transaction_repository(
        self, db_path: Optional[Path] = None
    ) -> SaleRepository:
        if not db_path:
            db_path = self.db_path
        repo = SaleRepository(db_path)
        return repo

    def get_transactions(self, customer: Customer) -> List[Sale]:
        repo = self.transaction_repository()
        transactions = repo.search_by_parent(customer)
        return transactions

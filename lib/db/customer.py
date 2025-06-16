import sqlite3
from pathlib import Path
from typing import Optional
from utils import get_db_path


class Customer:
    def __init__(self, id: Optional[int], name: str) -> None:
        self.id = id
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return False
        return self.id == other.id and self.name == other.name

    def __repr__(self):
        return f"Customer(id={self.id}, name='{self.name}')"


class CustomerRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def create(self, id: Optional[int], name: str) -> Customer:
        with self._connect() as conn:
            cursor = conn.cursor()
            if id is None:
                cursor.execute(
                    "INSERT INTO customers (name) VALUES (?)", (name,)
                )
            else:
                cursor.execute(
                    "INSERT INTO customers (id, name) VALUES (?, ?)",
                    (id, name),
                )
            conn.commit()
            return Customer(cursor.lastrowid if id is None else id, name)

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

    def update(self, id: int, name: str) -> Customer:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET name = ? WHERE id = ?", (name, id)
            )
            conn.commit()
            return self.read(id=id)

    def delete(self, id: int) -> Optional[Customer]:
        customer = self.read(id=id)
        if not customer:
            return None
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers WHERE id = ?", (id,))
            conn.commit()
            return customer

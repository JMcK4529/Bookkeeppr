import sqlite3
from pathlib import Path
from typing import Optional
from utils import get_db_path


class Sale:
    def __init__(
        self,
        id: Optional[int],
        customer_id: int,
        invoice_number: str,
        net_amount: float,
        vat_percent: str,
        payment_method: str,
        timestamp: str,
    ):
        self.id = id
        self.customer_id = customer_id
        self.invoice_number = invoice_number
        self.net_amount = net_amount
        self.vat_percent = vat_percent
        self.payment_method = payment_method
        self.timestamp = timestamp

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sale) and self.__dict__ == other.__dict__

    def __repr__(self):
        return f"Sale(id={self.id}, invoice_number='{self.invoice_number}')"


class SaleRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def create(self, sale: Sale) -> Sale:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sales (customer_id, invoice_number, net_amount, vat_percent, payment_method, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    sale.customer_id,
                    sale.invoice_number,
                    sale.net_amount,
                    sale.vat_percent,
                    sale.payment_method,
                    sale.timestamp,
                ),
            )
            conn.commit()
            return Sale(
                cursor.lastrowid,
                sale.customer_id,
                sale.invoice_number,
                sale.net_amount,
                sale.vat_percent,
                sale.payment_method,
                sale.timestamp,
            )

    def read(self, id: int) -> Optional[Sale]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, customer_id, invoice_number, net_amount, vat_percent, payment_method, timestamp FROM sales WHERE id = ?",
                (id,),
            )
            row = cursor.fetchone()
            return Sale(*row) if row else None

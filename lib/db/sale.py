import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from lib.db.utils import get_db_path, normalize_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Sale:
    def __init__(
        self,
        id: Optional[int],
        customer_id: int,
        customer_name: str,
        invoice_number: str,
        net_amount: float,
        vat_percent: float,
        payment_method: str,
        timestamp: Optional[str],
    ):
        self.id = id
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.invoice_number = invoice_number
        self.net_amount = net_amount
        self.vat_percent = vat_percent
        self.payment_method = payment_method
        self.timestamp = timestamp
        if timestamp:
            self.timestamp = normalize_datetime(timestamp)
        else:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sale) and self.__dict__ == other.__dict__

    def __repr__(self):
        return f"Sale(id={self.id}, invoice_number='{self.invoice_number}', customer_name='{self.customer_name}')"


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
                INSERT INTO sales (customer_id, customer_name, invoice_number, net_amount, vat_percent, payment_method, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    sale.customer_id,
                    sale.customer_name,
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
                sale.customer_name,
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
                "SELECT id, customer_id, customer_name, invoice_number, net_amount, vat_percent, payment_method, timestamp FROM sales WHERE id = ?",
                (id,),
            )
            row = cursor.fetchone()
            return Sale(*row) if row else None

    def search(self, filters: dict) -> list[Sale]:
        query = """
            SELECT id, customer_id, customer_name, invoice_number, net_amount, vat_percent, payment_method, timestamp
            FROM sales WHERE 1=1
        """
        params = []

        # Filter by customer name (if joined externally, skip here)
        if customer_substring := filters.get("customer"):
            query += " AND LOWER(customer_name) LIKE ?"
            params.append(f"%{customer_substring.lower()}%")

        # Filter by invoice_number
        if invoice_substring := filters.get("invoice"):
            query += " AND LOWER(invoice_number) LIKE ?"
            params.append(f"%{invoice_substring.lower()}%")

        # Filter by net amount
        net_filters = filters.get("net", {})
        if "eq" in net_filters:
            query += " AND net_amount = ?"
            params.append(net_filters["eq"])
        else:
            if "min" in net_filters:
                query += " AND net_amount >= ?"
                params.append(net_filters["min"])
            if "max" in net_filters:
                query += " AND net_amount <= ?"
                params.append(net_filters["max"])

        # Filter by vat_percent
        vat_filter = filters.get("vat")
        if vat_filter:
            placeholders = ",".join("?" for _ in vat_filter)
            query += f" AND vat_percent IN ({placeholders})"
            params.extend(vat_filter)

        # Filter by payment_method
        payment_filter = filters.get("payment")
        if payment_filter:
            placeholders = ",".join("?" for _ in payment_filter)
            query += f" AND payment_method IN ({placeholders})"
            params.extend(payment_filter)

        # Filter by timestamp
        timeFrom = normalize_datetime(filters.get("timeFrom"))
        timeTo = normalize_datetime(filters.get("timeTo"))
        if timeFrom:
            query += " AND timestamp >= ?"
            params.append(timeFrom)
        if timeTo:
            query += " AND timestamp <= ?"
            params.append(timeTo)

        logger.info(f"query={query},params={params}")

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Sale(*row) for row in rows]

    def all(self) -> list[Sale]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, customer_id, customer_name, invoice_number, net_amount, vat_percent, payment_method, timestamp 
                FROM sales
            """,
            )
            rows = cursor.fetchall()
            return [Sale(*row) for row in rows]

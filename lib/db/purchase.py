import sqlite3
from pathlib import Path
from typing import Optional
from utils import get_db_path


class Purchase:
    def __init__(
        self,
        id: Optional[int],
        supplier_id: int,
        supplier_invoice_code: str,
        internal_invoice_number: str,
        net_amount: float,
        vat_percent: str,
        goods: float,
        utilities: float,
        motor_expenses: float,
        sundries: float,
        payment_method: str,
        timestamp: str,
        capital_spend: bool,
    ):
        self.id = id
        self.supplier_id = supplier_id
        self.supplier_invoice_code = supplier_invoice_code
        self.internal_invoice_number = internal_invoice_number
        self.net_amount = net_amount
        self.vat_percent = vat_percent
        self.goods = goods
        self.utilities = utilities
        self.motor_expenses = motor_expenses
        self.sundries = sundries
        self.payment_method = payment_method
        self.timestamp = timestamp
        self.capital_spend = capital_spend

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Purchase) and self.__dict__ == other.__dict__

    def __repr__(self):
        return f"Purchase(id={self.id}, internal_invoice_number='{self.internal_invoice_number}')"


class PurchaseRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def create(self, purchase: Purchase) -> Purchase:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO purchases (
                    supplier_id, supplier_invoice_code, internal_invoice_number, net_amount,
                    vat_percent, goods, utilities, motor_expenses, sundries,
                    payment_method, timestamp, capital_spend
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    purchase.supplier_id,
                    purchase.supplier_invoice_code,
                    purchase.internal_invoice_number,
                    purchase.net_amount,
                    purchase.vat_percent,
                    purchase.goods,
                    purchase.utilities,
                    purchase.motor_expenses,
                    purchase.sundries,
                    purchase.payment_method,
                    purchase.timestamp,
                    int(purchase.capital_spend),
                ),
            )
            conn.commit()
            return Purchase(
                cursor.lastrowid,
                purchase.supplier_id,
                purchase.supplier_invoice_code,
                purchase.internal_invoice_number,
                purchase.net_amount,
                purchase.vat_percent,
                purchase.goods,
                purchase.utilities,
                purchase.motor_expenses,
                purchase.sundries,
                purchase.payment_method,
                purchase.timestamp,
                purchase.capital_spend,
            )

    def read(self, id: int) -> Optional[Purchase]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, supplier_id, supplier_invoice_code, internal_invoice_number, net_amount,
                       vat_percent, goods, utilities, motor_expenses, sundries,
                       payment_method, timestamp, capital_spend
                FROM purchases WHERE id = ?""",
                (id,),
            )
            row = cursor.fetchone()
            if row:
                # Convert capital_spend from int to bool
                row = list(row)
                row[-1] = bool(row[-1])
                return Purchase(*row)
            return None

    def update(self, purchase: Purchase) -> Optional[Purchase]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE purchases SET
                    supplier_id = ?, supplier_invoice_code = ?, internal_invoice_number = ?, net_amount = ?,
                    vat_percent = ?, goods = ?, utilities = ?, motor_expenses = ?, sundries = ?,
                    payment_method = ?, timestamp = ?, capital_spend = ?
                WHERE id = ?""",
                (
                    purchase.supplier_id,
                    purchase.supplier_invoice_code,
                    purchase.internal_invoice_number,
                    purchase.net_amount,
                    purchase.vat_percent,
                    purchase.goods,
                    purchase.utilities,
                    purchase.motor_expenses,
                    purchase.sundries,
                    purchase.payment_method,
                    purchase.timestamp,
                    int(purchase.capital_spend),
                    purchase.id,
                ),
            )
            conn.commit()
            return self.read(purchase.id)

    def delete(self, id: int) -> Optional[Purchase]:
        purchase = self.read(id)
        if not purchase:
            return None
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM purchases WHERE id = ?", (id,))
            conn.commit()
            return purchase

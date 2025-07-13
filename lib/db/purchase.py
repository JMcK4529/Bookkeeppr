import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from lib.db.transaction import Transaction, TransactionRepository
from lib.db.utils import get_db_path, normalize_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Purchase(Transaction):
    def __init__(
        self,
        id: Optional[int],
        supplier_id: int,
        supplier_name: str,
        supplier_invoice_code: str,
        internal_invoice_number: str,
        net_amount: float,
        vat_percent: float,
        goods: float,
        utilities: float,
        motor_expenses: float,
        sundries: float,
        miscellaneous: float,
        payment_method: str,
        timestamp: str,
        capital_spend: bool,
    ):
        # Fail fast if the cost breakdown is incorrect
        component_sum = sum(
            [goods, utilities, motor_expenses, sundries, miscellaneous]
        )
        if net_amount != round(component_sum, 2):
            raise ValueError(
                f"Net amount ({net_amount}) does not equal sum of components ({component_sum})."
            )
        self.id = id
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.supplier_invoice_code = supplier_invoice_code
        self.internal_invoice_number = internal_invoice_number
        self.net_amount = net_amount
        self.vat_percent = vat_percent
        self.goods = goods
        self.utilities = utilities
        self.motor_expenses = motor_expenses
        self.sundries = sundries
        self.miscellaneous = miscellaneous
        self.payment_method = payment_method
        self.timestamp = timestamp
        if timestamp:
            self.timestamp = normalize_datetime(timestamp)
        else:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.capital_spend = capital_spend

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Purchase) and self.__dict__ == other.__dict__

    def __repr__(self):
        return f"Purchase(id={self.id}, internal_invoice_number='{self.internal_invoice_number}', supplier_name='{self.supplier_name}')"


class PurchaseRepository(TransactionRepository[Purchase]):
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
                    supplier_id, supplier_name, supplier_invoice_code, internal_invoice_number, net_amount,
                    vat_percent, goods, utilities, motor_expenses, sundries, miscellaneous,
                    payment_method, timestamp, capital_spend
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    purchase.supplier_id,
                    purchase.supplier_name,
                    purchase.supplier_invoice_code,
                    purchase.internal_invoice_number,
                    purchase.net_amount,
                    purchase.vat_percent,
                    purchase.goods,
                    purchase.utilities,
                    purchase.motor_expenses,
                    purchase.sundries,
                    purchase.miscellaneous,
                    purchase.payment_method,
                    purchase.timestamp,
                    int(purchase.capital_spend),
                ),
            )
            conn.commit()
            return Purchase(
                cursor.lastrowid,
                purchase.supplier_id,
                purchase.supplier_name,
                purchase.supplier_invoice_code,
                purchase.internal_invoice_number,
                purchase.net_amount,
                purchase.vat_percent,
                purchase.goods,
                purchase.utilities,
                purchase.motor_expenses,
                purchase.sundries,
                purchase.miscellaneous,
                purchase.payment_method,
                purchase.timestamp,
                purchase.capital_spend,
            )

    def read(self, id: int) -> Optional[Purchase]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, supplier_id, supplier_name, supplier_invoice_code, internal_invoice_number, net_amount,
                       vat_percent, goods, utilities, motor_expenses, sundries, miscellaneous,
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
                    supplier_id = ?, supplier_name = ?, supplier_invoice_code = ?, internal_invoice_number = ?, net_amount = ?,
                    vat_percent = ?, goods = ?, utilities = ?, motor_expenses = ?, sundries = ?, miscellaneous = ?,
                    payment_method = ?, timestamp = ?, capital_spend = ?
                WHERE id = ?""",
                (
                    purchase.supplier_id,
                    purchase.supplier_name,
                    purchase.supplier_invoice_code,
                    purchase.internal_invoice_number,
                    purchase.net_amount,
                    purchase.vat_percent,
                    purchase.goods,
                    purchase.utilities,
                    purchase.motor_expenses,
                    purchase.sundries,
                    purchase.miscellaneous,
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

    def search(self, filters: dict) -> List[Purchase]:
        query = """
            SELECT id, supplier_id, supplier_name, supplier_invoice_code, internal_invoice_number, net_amount, vat_percent, goods, utilities, motor_expenses, sundries, miscellaneous, payment_method, timestamp, capital_spend
            FROM purchases WHERE 1=1
        """
        params = []
        logger.info(f"Query filters: {filters}")
        # Filter by supplier and/or invoice number
        substring_filters = {
            filters.get("supplier"): "supplier",
            filters.get("supplier_invoice"): "supplier_invoice_code",
            filters.get("internal_invoice"): "internal_invoice_number",
        }
        for substring in substring_filters.keys():
            if substring:
                query += f" AND LOWER({substring_filters[substring]})"
                params.append(f"%{substring.lower()}%")

        # Filter by cost or cost breakdown
        range_filters = [
            {"name": "net_amount", "values": filters.get("net", {})},
            {"name": "goods", "values": filters.get("goods", {})},
            {"name": "utilities", "values": filters.get("utilities", {})},
            {
                "name": "motor_expenses",
                "values": filters.get("motor_expenses", {}),
            },
            {"name": "sundries", "values": filters.get("sundries", {})},
            {
                "name": "miscellaneous",
                "values": filters.get("miscellaneous", {}),
            },
        ]
        logger.info(f"Range filters: {range_filters}")
        for range in range_filters:
            if "eq" in range["values"]:
                query += f" AND {range["name"]} = ?"
                params.append(range["values"]["eq"])
                logger.info(
                    f"Added {query},{range["values"]["eq"]} to query,params."
                )
            else:
                if "min" in range["values"]:
                    query += f" AND {range["name"]} >= ?"
                    params.append(range["values"]["min"])
                    logger.info(
                        f"Added {query},{range["values"]["min"]} to query,params."
                    )
                if "max" in range["values"]:
                    query += f" AND {range["name"]} <= ?"
                    params.append(range["values"]["max"])
                    logger.info(
                        f"Added {query},{range["values"]["max"]} to query,params."
                    )

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

        # Filter by capital spend
        if capital_spend := filters.get("capital_spend"):
            if capital_spend == "True":
                capital_spend = True
            if capital_spend == "False":
                capital_spend = False
            query += " AND capital_spend >= ?"
            params.append(int(capital_spend))

        logger.info(f"query={query},params={params}")

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Purchase(*row) for row in rows]

    def search_by_parent(self, entity) -> List[Purchase]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, supplier_id, supplier_name, supplier_invoice_code, internal_invoice_number, net_amount, vat_percent, goods, utilities, motor_expenses, sundries, miscellaneous, payment_method, timestamp, capital_spend
                FROM purchases WHERE supplier_id = ?
                """,
                (entity.id,),
            )
            rows = cursor.fetchall()
            return [Purchase(*row) for row in rows]

    def all(self) -> List[Purchase]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, supplier_id, supplier_name, supplier_invoice_code, internal_invoice_number, net_amount, vat_percent, goods, utilities, motor_expenses, sundries, miscellaneous, payment_method, timestamp, capital_spend 
                FROM purchases
            """,
            )
            rows = cursor.fetchall()
            return [Purchase(*row) for row in rows]

import pytest
from unittest.mock import MagicMock, patch
from unittest import TestCase
from tests.data_utils import get_test_data
from lib.db.sale import *


class TestSale(TestCase):
    def test_init_eq_repr(self):
        sale = Sale(
            id=1,
            customer_id=101,
            invoice_number="INV-2024-001",
            net_amount=100.00,
            vat_percent="20%",
            payment_method="Card",
            timestamp="2024-01-01 09:00:00",
        )
        self.assertEqual(sale.id, 1)
        self.assertEqual(sale.invoice_number, "INV-2024-001")
        self.assertEqual(
            sale,
            Sale(
                1,
                101,
                "INV-2024-001",
                100.00,
                "20%",
                "Card",
                "2024-01-01 09:00:00",
            ),
        )
        self.assertEqual(
            str(sale), "Sale(id=1, invoice_number='INV-2024-001')"
        )


class TestSaleRepository(TestCase):
    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_conn.__enter__.return_value.cursor.return_value = (
            self.mock_cursor
        )

        patcher = patch(
            "lib.db.sale.sqlite3.connect", return_value=self.mock_conn
        )
        self.mock_connect = patcher.start()
        self.addCleanup(patcher.stop)

        self.repo = SaleRepository(db_path=Path("/fake/path.db"))

    def test_create(self):
        self.mock_cursor.lastrowid = 77
        sale = Sale(
            None,
            202,
            "INV-2024-002",
            250.00,
            "0%",
            "BACS",
            "2024-01-02 10:00:00",
        )
        result = self.repo.create(sale)
        self.assertEqual(result.id, 77)
        self.assertEqual(result.invoice_number, "INV-2024-002")
        self.mock_cursor.execute.assert_called_once()

    def test_read_found(self):
        self.mock_cursor.fetchone.return_value = [
            6,
            203,
            "INV-2024-003",
            500.0,
            "20%",
            "Cheque",
            "2024-01-03 14:00:00",
        ]
        result = self.repo.read(6)
        self.assertIsInstance(result, Sale)
        self.assertEqual(result.id, 6)
        self.assertEqual(result.invoice_number, "INV-2024-003")
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, customer_id, invoice_number, net_amount, vat_percent, payment_method, timestamp FROM sales WHERE id = ?",
            (6,),
        )

    def test_read_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        result = self.repo.read(404)
        self.assertIsNone(result)
        self.mock_cursor.execute.assert_called_once()

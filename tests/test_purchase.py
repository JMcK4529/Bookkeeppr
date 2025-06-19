import pytest
from unittest.mock import MagicMock, patch
from unittest import TestCase
from tests.data_utils import get_test_data
from lib.db.purchase import *


class TestPurchase(TestCase):
    def test_init_eq_repr(self):
        purchase = Purchase(
            id=1,
            supplier_id=2,
            supplier_invoice_code="S123",
            internal_invoice_number="I456",
            net_amount=100.0,
            vat_percent="20%",
            goods=50.0,
            utilities=10.0,
            motor_expenses=20.0,
            sundries=20.0,
            payment_method="BACS",
            timestamp="2024-01-01 12:00:00",
            capital_spend=True,
        )
        self.assertEqual(purchase.id, 1)
        self.assertEqual(purchase.internal_invoice_number, "I456")
        self.assertEqual(
            purchase,
            Purchase(
                1,
                2,
                "S123",
                "I456",
                100.0,
                "20%",
                50.0,
                10.0,
                20.0,
                20.0,
                "BACS",
                "2024-01-01 12:00:00",
                True,
            ),
        )
        self.assertEqual(
            str(purchase), "Purchase(id=1, internal_invoice_number='I456')"
        )


class TestPurchaseRepository(TestCase):
    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_conn.__enter__.return_value.cursor.return_value = (
            self.mock_cursor
        )

        patcher = patch(
            "lib.db.purchase.sqlite3.connect", return_value=self.mock_conn
        )
        self.mock_connect = patcher.start()
        self.addCleanup(patcher.stop)

        self.repo = PurchaseRepository(db_path=Path("/fake/path.db"))

    def test_create(self):
        self.mock_cursor.lastrowid = 99
        purchase = Purchase(
            None,
            1,
            "S123",
            "I789",
            200.0,
            "20%",
            120.0,
            20.0,
            30.0,
            30.0,
            "Card",
            "2024-01-01",
            False,
        )
        result = self.repo.create(purchase)
        self.assertEqual(result.id, 99)
        self.assertEqual(result.internal_invoice_number, "I789")
        self.mock_cursor.execute.assert_called_once()

    def test_read(self):
        self.mock_cursor.fetchone.return_value = [
            1,
            2,
            "S456",
            "I123",
            250.0,
            "0%",
            100.0,
            30.0,
            70.0,
            50.0,
            "Cheque",
            "2024-01-02",
            1,
        ]
        result = self.repo.read(1)
        self.assertTrue(result.capital_spend)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.internal_invoice_number, "I123")

    def test_update(self):
        purchase = Purchase(
            10,
            2,
            "SUPP",
            "INT-999",
            300.0,
            "20%",
            150.0,
            50.0,
            50.0,
            50.0,
            "BACS",
            "2024-01-05",
            True,
        )
        with patch.object(self.repo, "read", return_value=purchase):
            result = self.repo.update(purchase)
            self.assertEqual(result, purchase)
            self.mock_cursor.execute.assert_called_once()

    def test_delete_exists(self):
        purchase = Purchase(
            5,
            1,
            "SUP",
            "INTX",
            150.0,
            "0%",
            80.0,
            20.0,
            25.0,
            25.0,
            "Direct Debit",
            "2024-01-03",
            False,
        )
        with patch.object(self.repo, "read", return_value=purchase):
            result = self.repo.delete(5)
            self.assertEqual(result, purchase)
            self.mock_cursor.execute.assert_called_once_with(
                "DELETE FROM purchases WHERE id = ?", (5,)
            )

    def test_delete_not_exists(self):
        with patch.object(self.repo, "read", return_value=None):
            result = self.repo.delete(404)
            self.assertIsNone(result)
            self.mock_cursor.execute.assert_not_called()

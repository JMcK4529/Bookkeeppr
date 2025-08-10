import os
import pytest
from random import randint
from unittest.mock import MagicMock, patch
from unittest import TestCase
from tests.data_utils import get_test_data
from lib.db.purchase import *


DATA_DIR = f"{os.path.dirname(__file__)}/data/db.purchase"


class TestPurchase(TestCase):
    def test_init_eq_repr(self):
        test_cases = get_test_data(f"{DATA_DIR}/Purchase.txt")
        for params in test_cases:
            with self.subTest(params=params):
                purchase = Purchase(**params)
                self.assertEqual(purchase.id, params["id"])
                self.assertEqual(
                    purchase.internal_invoice_number,
                    params["internal_invoice_number"],
                )
                self.assertEqual(
                    purchase,
                    Purchase(*params.values()),
                )
                self.assertEqual(
                    str(purchase),
                    f"Purchase(id={params['id']}, internal_invoice_number='{params['internal_invoice_number']}', supplier_name='{params['supplier_name']}')",
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

    def test_connect(self):
        with patch("lib.db.purchase.sqlite3.connect") as mock_connect:
            self.repo._connect()
        mock_connect.assert_called_once_with(self.repo.db_path)

    def test_create(self):
        test_cases = get_test_data(f"{DATA_DIR}/create.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                if params["id"] is None:
                    self.mock_cursor.lastrowid = randint(0, 100)
                    args = [
                        "supplier_id, supplier_name, supplier_invoice_code, internal_invoice_number, net_amount, vat_percent, goods, utilities, motor_expenses, sundries, miscellaneous, payment_method, timestamp, capital_spend",
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (*list(params.values())[1:],),
                    ]
                    expected = Purchase(
                        self.mock_cursor.lastrowid, *list(params.values())[1:]
                    )
                else:
                    args = [
                        "id, supplier_id, supplier_name, supplier_invoice_code, internal_invoice_number, net_amount, vat_percent, goods, utilities, motor_expenses, sundries, miscellaneous, payment_method, timestamp, capital_spend",
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (*params.values(),),
                    ]
                purchase = Purchase(**params)
                result = self.repo.create(purchase)
                self.assertEqual(
                    result.id, params["id"] or self.mock_cursor.lastrowid
                )
                self.assertEqual(
                    result.internal_invoice_number,
                    params["internal_invoice_number"],
                )
                assert self.mock_cursor.execute.call_count == 1
                exec_call_args = self.mock_cursor.execute.call_args_list[
                    0
                ].args
                assert "INSERT INTO purchases (" in exec_call_args[0]
                for arg in args[0].split(", "):
                    assert arg in exec_call_args[0]
                assert f") VALUES {args[1]}" in exec_call_args[0]
                assert exec_call_args[1] == args[2]

    def test_read_found(self):
        test_cases = get_test_data(f"{DATA_DIR}/read.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                self.mock_cursor.fetchone.return_value = list(params.values())
                result = self.repo.read(params["id"])
                self.assertIsInstance(result, Purchase)
                self.assertEqual(result.id, params["id"])
                self.assertEqual(
                    result.internal_invoice_number,
                    params["internal_invoice_number"],
                )
                assert self.mock_cursor.execute.call_count == 1
                exec_call_args = self.mock_cursor.execute.call_args_list[
                    0
                ].args
                assert "SELECT " in exec_call_args[0]
                for arg in [
                    "id",
                    "supplier_id",
                    "supplier_name",
                    "supplier_invoice_code",
                    "internal_invoice_number",
                    "net_amount",
                    "vat_percent",
                    "goods",
                    "utilities",
                    "motor_expenses",
                    "sundries",
                    "miscellaneous",
                    "payment_method",
                    "timestamp",
                    "capital_spend",
                ]:
                    assert arg in exec_call_args[0]
                assert "FROM purchases WHERE id = ?"
                assert exec_call_args[1] == (params["id"],)

    def test_read_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        result = self.repo.read(404)
        self.assertIsNone(result)
        self.mock_cursor.execute.assert_called_once()

    def test_update(self):
        test_cases = get_test_data(f"{DATA_DIR}/update.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                purchase = Purchase(**params)
                with patch.object(
                    self.repo, "read", return_value=purchase
                ) as mock_read:
                    result = self.repo.update(purchase)

                exec_call = self.mock_cursor.execute.call_args_list[0]
                query = exec_call.args[0]
                query_data = exec_call.args[1]

                assert "UPDATE purchases SET" in query
                for key in list(params.keys())[1:]:
                    assert f"{key} = ?" in query
                assert "WHERE id = ?" in query

                assert query_data == (*list(params.values())[1:], params["id"])
                self.assertEqual(result, purchase)
                mock_read.assert_called_once_with(purchase.id)

    def test_delete_when_exists(self):
        test_cases = get_test_data(f"{DATA_DIR}/delete.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                purchase = Purchase(**params)
                with patch.object(
                    self.repo, "read", return_value=purchase
                ) as mock_read:
                    result = self.repo.delete(purchase.id)

                self.mock_cursor.execute.assert_called_once_with(
                    "DELETE FROM purchases WHERE id = ?",
                    (purchase.id,),
                )
                self.assertEqual(result, purchase)
                mock_read.assert_called_once_with(purchase.id)

    def test_delete_when_not_exists(self):
        with patch.object(self.repo, "read", return_value=None):
            result = self.repo.delete(999)
            self.assertIsNone(result)
            self.mock_cursor.execute.assert_not_called()

    def test_search(self):
        test_cases = get_test_data(f"{DATA_DIR}/search.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                mock_row = (
                    1,
                    3001,
                    "Test Supplier",
                    "SUP-INV",
                    "INT-INV",
                    142.50,
                    "20%",
                    100.0,
                    20.0,
                    15.0,
                    5.0,
                    2.5,
                    "Bank",
                    "2024-01-15 10:30:00",
                    1,
                )
                self.mock_cursor.fetchall.return_value = [mock_row]

                results = self.repo.search(params)

                self.assertEqual(len(results), 1)
                self.assertIsInstance(results[0], Purchase)
                self.assertEqual(results[0].supplier_name, "Test Supplier")

                query, args = self.mock_cursor.execute.call_args.args

                # Substring filters
                if "supplier" in params:
                    self.assertIn("LOWER(supplier_name)", query)
                    self.assertIn(f"%{params['supplier'].lower()}%", args)

                if "supplier_invoice" in params:
                    self.assertIn("LOWER(supplier_invoice_code)", query)
                    self.assertIn(
                        f"%{params['supplier_invoice'].lower()}%", args
                    )

                if "internal_invoice" in params:
                    self.assertIn("LOWER(internal_invoice_number)", query)
                    self.assertIn(
                        f"%{params['internal_invoice'].lower()}%", args
                    )

                # Range filters
                for field in [
                    "net",
                    "goods",
                    "utilities",
                    "motor_expenses",
                    "sundries",
                    "miscellaneous",
                ]:
                    if field in params:
                        field_name = field if field != "net" else "net_amount"
                        values = params[field]
                        if "eq" in values:
                            self.assertIn(f"{field_name} = ?", query)
                            self.assertIn(values["eq"], args)
                        else:
                            if "min" in values:
                                self.assertIn(f"{field_name} >= ?", query)
                                self.assertIn(values["min"], args)
                            if "max" in values:
                                self.assertIn(f"{field_name} <= ?", query)
                                self.assertIn(values["max"], args)

                if "vat" in params:
                    self.assertIn("vat_percent IN", query)
                    for val in params["vat"]:
                        self.assertIn(val, args)

                if "payment" in params:
                    self.assertIn("payment_method IN", query)
                    for method in params["payment"]:
                        self.assertIn(method, args)

                if "timeFrom" in params:
                    self.assertIn("timestamp >= ?", query)
                    self.assertIn(normalize_datetime(params["timeFrom"]), args)

                if "timeTo" in params:
                    self.assertIn("timestamp <= ?", query)
                    self.assertIn(normalize_datetime(params["timeTo"]), args)

                if "capital_spend" in params:
                    self.assertIn("capital_spend >= ?", query)
                    self.assertIn(int(params["capital_spend"] == "True"), args)

    def test_search_by_parent_purchase(self):
        test_cases = get_test_data(f"{DATA_DIR}/search_by_parent.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                supplier_params = params["supplier"]
                purchases = params["purchases"]
                supplier = MagicMock(**supplier_params)

                with patch.object(
                    self.mock_cursor,
                    "fetchall",
                    return_value=[list(p.values()) for p in purchases],
                ) as mock_fetchall:
                    result = self.repo.search_by_parent(supplier)

                exec_call = self.mock_cursor.execute.call_args_list[0]
                query = exec_call.args[0]
                query_data = exec_call.args[1]

                if purchases:
                    assert "SELECT" in query
                    for key in list(purchases[0].keys())[:-1]:
                        assert f"{key}," in query
                    assert f"{list(purchases[0].keys())[-1]}" in query
                    assert "FROM purchases WHERE supplier_id = ?" in query

                assert query_data == (supplier_params["id"],)
                self.assertEqual(result, [Purchase(**p) for p in purchases])
                mock_fetchall.assert_called_once()

    def test_all(self):
        test_cases = get_test_data(f"{DATA_DIR}/all.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                purchases = params["purchases"]
                rows = [(*list(purchase.values()),) for purchase in purchases]
                self.mock_cursor.fetchall.return_value = rows
                result = self.repo.all()
                exec_call_arg = self.mock_cursor.execute.call_args_list[
                    0
                ].args[0]
                assert "SELECT id," in exec_call_arg
                for i in [
                    "supplier_id",
                    "supplier_name",
                    "supplier_invoice_code",
                    "internal_invoice_number",
                    "net_amount",
                    "vat_percent",
                    "goods",
                    "utilities",
                    "motor_expenses",
                    "sundries",
                    "miscellaneous",
                    "payment_method",
                ]:
                    assert f"{i}," in exec_call_arg
                assert "timestamp" in exec_call_arg
                assert "FROM purchases" in exec_call_arg
                self.assertEqual(
                    result,
                    [Purchase(*purchase_args) for purchase_args in rows],
                )

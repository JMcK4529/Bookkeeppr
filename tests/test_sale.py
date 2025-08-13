import os
import pytest
from random import randint
from unittest.mock import MagicMock, patch
from unittest import TestCase
from tests.data_utils import get_test_data
from lib.db.sale import *


DATA_DIR = f"{os.path.dirname(__file__)}/data/db.sale"


class TestSale(TestCase):
    def test_init_eq_repr(self):
        test_cases = get_test_data(f"{DATA_DIR}/Sale.txt")
        for params in test_cases:
            with self.subTest(params=params):
                sale = Sale(**params)
                self.assertEqual(sale.id, params["id"])
                self.assertEqual(sale.invoice_number, params["invoice_number"])
                self.assertEqual(
                    sale,
                    Sale(*params.values()),
                )
                self.assertEqual(
                    str(sale),
                    f"Sale(id={params['id']}, invoice_number='{params['invoice_number']}', customer_name='{params['customer_name']}')",
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

    def test_connect(self):
        with patch("lib.db.sale.sqlite3.connect") as mock_connect:
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
                        "(customer_id, customer_name, invoice_number, net_amount, vat_percent, payment_method, timestamp)",
                        "(?, ?, ?, ?, ?, ?, ?)",
                        (*list(params.values())[1:],),
                    ]
                    expected = Sale(
                        self.mock_cursor.lastrowid, *list(params.values())[1:]
                    )
                else:
                    args = [
                        "(id, customer_id, customer_name, invoice_number, net_amount, vat_percent, payment_method, timestamp)",
                        "(?, ?, ?, ?, ?, ?, ?, ?)",
                        (*params.values(),),
                    ]
                sale = Sale(**params)
                result = self.repo.create(sale)
                self.assertEqual(
                    result.id, params["id"] or self.mock_cursor.lastrowid
                )
                self.assertEqual(
                    result.invoice_number, params["invoice_number"]
                )
                assert self.mock_cursor.execute.call_count == 1
                exec_call_args = self.mock_cursor.execute.call_args_list[
                    0
                ].args
                assert f"INSERT INTO sales {args[0]}" in exec_call_args[0]
                assert f"VALUES {args[1]}" in exec_call_args[0]
                assert exec_call_args[1] == args[2]

    def test_read_found(self):
        test_cases = get_test_data(f"{DATA_DIR}/read.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                self.mock_cursor.fetchone.return_value = list(params.values())
                [
                    6,
                    203,
                    "INV-2024-003",
                    500.0,
                    "20%",
                    "Cheque",
                    "2024-01-03 14:00:00",
                ]
                result = self.repo.read(params["id"])
                self.assertIsInstance(result, Sale)
                self.assertEqual(result.id, params["id"])
                self.assertEqual(
                    result.invoice_number, params["invoice_number"]
                )
                self.mock_cursor.execute.assert_called_once_with(
                    "SELECT id, customer_id, customer_name, invoice_number, net_amount, vat_percent, payment_method, timestamp FROM sales WHERE id = ?",
                    (params["id"],),
                )

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
                sale = Sale(**params)
                with patch.object(
                    self.repo, "read", return_value=sale
                ) as mock_read:
                    result = self.repo.update(sale)

                exec_call = self.mock_cursor.execute.call_args_list[0]
                query = exec_call.args[0]
                query_data = exec_call.args[1]

                assert "UPDATE sales SET" in query
                for key in list(params.keys())[1:]:
                    assert f"{key} = ?" in query
                assert "WHERE id = ?" in query

                assert query_data == (*list(params.values())[1:], params["id"])
                self.assertEqual(result, sale)
                mock_read.assert_called_once_with(sale.id)

    def test_delete_when_exists(self):
        test_cases = get_test_data(f"{DATA_DIR}/delete.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                sale = Sale(**params)
                with patch.object(
                    self.repo, "read", return_value=sale
                ) as mock_read:
                    result = self.repo.delete(sale.id)

                self.mock_cursor.execute.assert_called_once_with(
                    "DELETE FROM sales WHERE id = ?",
                    (sale.id,),
                )
                self.assertEqual(result, sale)
                mock_read.assert_called_once_with(sale.id)

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
                    2001,
                    "Test Customer",
                    "INV-TEST",
                    123.45,
                    "20%",
                    "Card",
                    "2024-01-15 10:30:00",
                )
                self.mock_cursor.fetchall.return_value = [mock_row]

                results = self.repo.search(params)

                # Validate the results
                self.assertEqual(len(results), 1)
                self.assertIsInstance(results[0], Sale)
                self.assertEqual(results[0].customer_name, "Test Customer")

                # Validate query and parameters
                query, params = self.mock_cursor.execute.call_args.args

                if "customer" in params:
                    self.assertIn("LOWER(customer_name) LIKE ?", query)
                    self.assertIn(f"%{params['customer'].lower()}%", params)

                if "invoice" in params:
                    self.assertIn("LOWER(invoice_number) LIKE ?", query)
                    self.assertIn(f"%{params['invoice'].lower()}%", params)

                if "net" in params:
                    net = params["net"]
                    if "eq" in net:
                        self.assertIn("net_amount = ?", query)
                        self.assertIn(net["eq"], params)
                    else:
                        if "min" in net:
                            self.assertIn("net_amount >= ?", query)
                            self.assertIn(net["min"], params)
                        if "max" in net:
                            self.assertIn("net_amount <= ?", query)
                            self.assertIn(net["max"], params)

                if "vat" in params:
                    for val in params["vat"]:
                        self.assertIn(val, params)
                    self.assertIn("vat_percent IN", query)

                if "payment" in params:
                    for method in params["payment"]:
                        self.assertIn(method, params)
                    self.assertIn("payment_method IN", query)

                if "timeFrom" in params:
                    self.assertIn("timestamp >= ?", query)
                    self.assertIn(
                        normalize_datetime(params["timeFrom"]), params
                    )

                if "timeTo" in params:
                    self.assertIn("timestamp <= ?", query)
                    self.assertIn(normalize_datetime(params["timeTo"]), params)

    def test_search_by_parent(self):
        test_cases = get_test_data(f"{DATA_DIR}/search_by_parent.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                customer_params = params["customer"]
                sales = params["sales"]
                customer = MagicMock(**customer_params)
                with patch.object(
                    self.mock_cursor,
                    "fetchall",
                    return_value=[list(sale.values()) for sale in sales],
                ) as mock_fetchall:
                    result = self.repo.search_by_parent(customer)

                exec_call = self.mock_cursor.execute.call_args_list[0]
                query = exec_call.args[0]
                query_data = exec_call.args[1]

                if sales:
                    assert "SELECT" in query
                    for key in list(sales[0].keys())[:-1]:
                        assert f"{key}," in query
                    assert f"{list(sales[0].keys())[-1]}" in query
                    assert "FROM sales WHERE customer_id = ?" in query

                assert query_data == (customer_params["id"],)
                self.assertEqual(result, [Sale(**sale) for sale in sales])
                mock_fetchall.assert_called_once()

    def test_all(self):
        test_cases = get_test_data(f"{DATA_DIR}/all.txt")
        for params in test_cases:
            self.setUp()
            with self.subTest(params=params):
                sales = params["sales"]
                rows = [(*list(sale.values()),) for sale in sales]
                self.mock_cursor.fetchall.return_value = rows
                result = self.repo.all()
                exec_call_arg = self.mock_cursor.execute.call_args_list[
                    0
                ].args[0]
                assert "SELECT id," in exec_call_arg
                for i in [
                    "customer_id",
                    "customer_name",
                    "invoice_number",
                    "net_amount",
                    "vat_percent",
                    "payment_method",
                ]:
                    assert f"{i}," in exec_call_arg
                assert "timestamp" in exec_call_arg
                assert "FROM sales" in exec_call_arg
                self.assertEqual(
                    result,
                    [Sale(*sale_args) for sale_args in rows],
                )

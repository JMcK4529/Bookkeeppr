import os
import pytest
from unittest.mock import MagicMock, patch
from unittest import TestCase
from tests.data_utils import get_test_data
from lib.db.customer import *

DATA_DIR = f"{os.path.dirname(__file__)}/data/db.customer"


class TestCustomer(TestCase):
    def test_init(self):
        test_cases = [{"id": i, "name": f"Customer_{i}"} for i in range(3)]
        for params in test_cases:
            with self.subTest(params=params):
                id = params.get("id")
                name = params.get("name")
                customer = Customer(id, name)
                assert customer.id == id
                assert customer.name == name

    def test_eq(self):
        test_cases = [
            {"ids": (i, j), "names": (f"Customer_{i}", f"Customer_{j}")}
            for i in range(2)
            for j in range(2)
        ]
        for params in test_cases:
            with self.subTest(params=params):
                id_1, id_2 = params.get("ids")
                name_1, name_2 = params.get("names")
                customer_1 = Customer(id_1, name_1)
                customer_2 = Customer(id_2, name_2)
                if id_1 == id_2:
                    assert customer_1 == customer_2
                    assert customer_1.name == customer_2.name
                else:
                    assert customer_1 != customer_2

    def test_repr(self):
        test_cases = [{"id": i, "name": f"Customer_{i}"} for i in range(3)]
        for params in test_cases:
            with self.subTest(params=params):
                id = params.get("id")
                name = params.get("name")
                customer = Customer(id, name)
                assert str(customer) == f"Customer(id={id}, name='{name}')"


class TestCustomerRepository(TestCase):
    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_conn.__enter__.return_value.cursor.return_value = (
            self.mock_cursor
        )

        patcher = patch(
            "lib.db.customer.sqlite3.connect", return_value=self.mock_conn
        )
        self.mock_connect = patcher.start()
        self.addCleanup(patcher.stop)

        self.repo = CustomerRepository(db_path=Path("/fake/db/path.db"))

    def test_connect(self):
        with patch("lib.db.customer.sqlite3.connect") as mock_connect:
            self.repo._connect()
        mock_connect.assert_called_once_with(self.repo.db_path)

    def test_create(self):
        customer = Customer(None, "CreateMe")
        result = self.repo.create(customer)

        if customer.id is None:
            args = ["(name)", "(?)", (customer.name,)]
            expected = Customer(self.mock_cursor.lastrowid, customer.name)
        else:
            args = ["(id, name)", "(?, ?)", (customer.id, customer.name)]
            expected = customer
        self.mock_cursor.execute.assert_called_once_with(
            f"INSERT INTO customers {args[0]} VALUES {args[1]}", args[2]
        )
        assert result == expected

    def test_read_by_id(self):
        self.mock_cursor.fetchone.return_value = (1, "Alice")
        result = self.repo.read(id=1)
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM customers WHERE id = ?", (1,)
        )
        self.assertEqual(result, Customer(1, "Alice"))

    def test_read_by_name(self):
        self.mock_cursor.fetchone.return_value = (2, "Bob")
        result = self.repo.read(name="Bob")
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM customers WHERE name = ?", ("Bob",)
        )
        self.assertEqual(result, Customer(2, "Bob"))

    def test_read_raises_if_no_params(self):
        with self.assertRaises(ValueError):
            self.repo.read()

    def test_update(self):
        customer = Customer(2, "Updated")
        with patch.object(
            self.repo, "read", return_value=customer
        ) as mock_read:
            result = self.repo.update(customer)

        exec_calls = self.mock_cursor.execute.call_args_list
        assert exec_calls[0].args == (
            "UPDATE customers SET name = ? WHERE id = ?",
            (customer.name, customer.id),
        )
        assert exec_calls[1].args == (
            "UPDATE sales SET customer_name = ? WHERE customer_id = ?",
            (customer.name, customer.id),
        )
        self.assertEqual(result, customer)
        mock_read.assert_called_once_with(id=customer.id)

    def test_delete_when_exists(self):
        customer = Customer(3, "DeleteMe")
        with patch.object(
            self.repo, "read", return_value=customer
        ) as mock_read:
            result = self.repo.delete(customer.id)

        exec_calls = self.mock_cursor.execute.call_args_list
        assert exec_calls[0].args == (
            "DELETE FROM customers WHERE id = ?",
            (customer.id,),
        )
        assert exec_calls[1].args == (
            "DELETE FROM sales WHERE customer_id = ?",
            (customer.id,),
        )
        self.assertEqual(result, customer)
        mock_read.assert_called_once_with(id=customer.id)

    def test_delete_when_not_exists(self):
        with patch.object(self.repo, "read", return_value=None):
            result = self.repo.delete(999)
            self.assertIsNone(result)
            self.mock_cursor.execute.assert_not_called()

    def test_search_when_exists(self):
        self.mock_cursor.fetchall.return_value = [
            (1, "OneTwoThree"),
            (2, "onetwothree"),
            (3, "twothreefour"),
        ]
        result = self.repo.search(name_query="two")
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM customers WHERE LOWER(name) LIKE ?",
            ("%two%",),
        )
        self.assertEqual(
            result,
            [
                Customer(1, "OneTwoThree"),
                Customer(2, "onetwothree"),
                Customer(3, "twothreefour"),
            ],
        )

    def test_search_when_not_exists(self):
        self.mock_cursor.fetchall.return_value = []
        result = self.repo.search(name_query="one")
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM customers WHERE LOWER(name) LIKE ?",
            ("%one%",),
        )
        self.assertEqual(
            result,
            [],
        )

    def test_all(self):
        self.mock_cursor.fetchall.return_value = [
            (1, "OneTwoThree"),
            (2, "onetwothree"),
            (3, "twothreefour"),
        ]
        result = self.repo.all()
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM customers"
        )
        self.assertEqual(
            result,
            [
                Customer(1, "OneTwoThree"),
                Customer(2, "onetwothree"),
                Customer(3, "twothreefour"),
            ],
        )

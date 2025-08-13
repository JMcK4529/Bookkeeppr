import os
import pytest
from unittest.mock import MagicMock, patch
from unittest import TestCase
from tests.data_utils import get_test_data
from lib.db.supplier import *

DATA_DIR = f"{os.path.dirname(__file__)}/data/db.supplier"


class TestSupplier(TestCase):
    def test_init(self):
        test_cases = [{"id": i, "name": f"Supplier_{i}"} for i in range(3)]
        for params in test_cases:
            with self.subTest(params=params):
                id = params.get("id")
                name = params.get("name")
                supplier = Supplier(id, name)
                assert supplier.id == id
                assert supplier.name == name

    def test_eq(self):
        test_cases = [
            {"ids": (i, j), "names": (f"Supplier_{i}", f"Supplier_{j}")}
            for i in range(2)
            for j in range(2)
        ]
        for params in test_cases:
            with self.subTest(params=params):
                id_1, id_2 = params.get("ids")
                name_1, name_2 = params.get("names")
                supplier_1 = Supplier(id_1, name_1)
                supplier_2 = Supplier(id_2, name_2)
                if id_1 == id_2:
                    assert supplier_1 == supplier_2
                    assert supplier_1.name == supplier_2.name
                else:
                    assert supplier_1 != supplier_2

    def test_repr(self):
        test_cases = [{"id": i, "name": f"Supplier_{i}"} for i in range(3)]
        for params in test_cases:
            with self.subTest(params=params):
                id = params.get("id")
                name = params.get("name")
                supplier = Supplier(id, name)
                assert str(supplier) == f"Supplier(id={id}, name='{name}')"


class TestSupplierRepository(TestCase):
    def setUp(self):
        self.mock_cursor = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_conn.__enter__.return_value.cursor.return_value = (
            self.mock_cursor
        )

        patcher = patch(
            "lib.db.supplier.sqlite3.connect", return_value=self.mock_conn
        )
        self.mock_connect = patcher.start()
        self.addCleanup(patcher.stop)

        self.repo = SupplierRepository(db_path=Path("/fake/db/path.db"))

    def test_connect(self):
        with patch("lib.db.supplier.sqlite3.connect") as mock_connect:
            self.repo._connect()
        mock_connect.assert_called_once_with(self.repo.db_path)

    def test_create(self):
        supplier = Supplier(None, "CreateMe")
        result = self.repo.create(supplier)

        if supplier.id is None:
            args = ["(name)", "(?)", (supplier.name,)]
            expected = Supplier(self.mock_cursor.lastrowid, supplier.name)
        else:
            args = ["(id, name)", "(?, ?)", (supplier.id, supplier.name)]
            expected = supplier
        self.mock_cursor.execute.assert_called_once_with(
            f"INSERT INTO suppliers {args[0]} VALUES {args[1]}", args[2]
        )
        assert result == expected

    def test_read_by_id(self):
        self.mock_cursor.fetchone.return_value = (1, "Alice")
        result = self.repo.read(id=1)
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM suppliers WHERE id = ?", (1,)
        )
        self.assertEqual(result, Supplier(1, "Alice"))

    def test_read_by_name(self):
        self.mock_cursor.fetchone.return_value = (2, "Bob")
        result = self.repo.read(name="Bob")
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM suppliers WHERE name = ?", ("Bob",)
        )
        self.assertEqual(result, Supplier(2, "Bob"))

    def test_read_raises_if_no_params(self):
        with self.assertRaises(ValueError):
            self.repo.read()

    def test_update(self):
        supplier = Supplier(2, "Updated")
        with patch.object(
            self.repo, "read", return_value=supplier
        ) as mock_read:
            result = self.repo.update(supplier)

        exec_calls = self.mock_cursor.execute.call_args_list
        assert exec_calls[0].args == (
            "UPDATE suppliers SET name = ? WHERE id = ?",
            (supplier.name, supplier.id),
        )
        assert exec_calls[1].args == (
            "UPDATE purchases SET supplier_name = ? WHERE supplier_id = ?",
            (supplier.name, supplier.id),
        )
        self.assertEqual(result, supplier)
        mock_read.assert_called_once_with(id=supplier.id)

    def test_delete_when_exists(self):
        supplier = Supplier(3, "DeleteMe")
        with patch.object(
            self.repo, "read", return_value=supplier
        ) as mock_read:
            result = self.repo.delete(supplier.id)

        exec_calls = self.mock_cursor.execute.call_args_list
        assert exec_calls[0].args == (
            "DELETE FROM suppliers WHERE id = ?",
            (supplier.id,),
        )
        assert exec_calls[1].args == (
            "DELETE FROM purchases WHERE supplier_id = ?",
            (supplier.id,),
        )
        self.assertEqual(result, supplier)
        mock_read.assert_called_once_with(id=supplier.id)

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
            "SELECT id, name FROM suppliers WHERE LOWER(name) LIKE ?",
            ("%two%",),
        )
        self.assertEqual(
            result,
            [
                Supplier(1, "OneTwoThree"),
                Supplier(2, "onetwothree"),
                Supplier(3, "twothreefour"),
            ],
        )

    def test_search_when_not_exists(self):
        self.mock_cursor.fetchall.return_value = []
        result = self.repo.search(name_query="one")
        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM suppliers WHERE LOWER(name) LIKE ?",
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
            "SELECT id, name FROM suppliers"
        )
        self.assertEqual(
            result,
            [
                Supplier(1, "OneTwoThree"),
                Supplier(2, "onetwothree"),
                Supplier(3, "twothreefour"),
            ],
        )

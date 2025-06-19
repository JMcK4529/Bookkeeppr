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

    def test_create_without_id(self):
        self.mock_cursor.lastrowid = 42
        result = self.repo.create(id=None, name="Alice")
        self.mock_cursor.execute.assert_called_once_with(
            "INSERT INTO suppliers (name) VALUES (?)", ("Alice",)
        )
        self.assertEqual(result, Supplier(42, "Alice"))

    def test_create_with_id(self):
        result = self.repo.create(id=5, name="Bob")
        self.mock_cursor.execute.assert_called_once_with(
            "INSERT INTO suppliers (id, name) VALUES (?, ?)", (5, "Bob")
        )
        self.assertEqual(result, Supplier(5, "Bob"))

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
        with patch.object(
            self.repo, "read", return_value=Supplier(1, "UpdatedName")
        ) as mock_read:
            result = self.repo.update(id=1, name="UpdatedName")
            self.mock_cursor.execute.assert_called_once_with(
                "UPDATE suppliers SET name = ? WHERE id = ?",
                ("UpdatedName", 1),
            )
            self.assertEqual(result, Supplier(1, "UpdatedName"))
            mock_read.assert_called_once_with(id=1)

    def test_delete_when_exists(self):
        supplier = Supplier(3, "DeleteMe")
        with patch.object(
            self.repo, "read", return_value=supplier
        ) as mock_read:
            result = self.repo.delete(3)
            self.mock_cursor.execute.assert_called_once_with(
                "DELETE FROM suppliers WHERE id = ?", (3,)
            )
            self.assertEqual(result, supplier)
            mock_read.assert_called_once_with(id=3)

    def test_delete_when_not_exists(self):
        with patch.object(self.repo, "read", return_value=None):
            result = self.repo.delete(999)
            self.assertIsNone(result)
            self.mock_cursor.execute.assert_not_called()

from unittest import TestCase
from unittest.mock import MagicMock
from lib.db.entity import *
from lib.db.transaction import *


class DummyEntity(Entity):
    def __init__(self, id: Optional[int], name: str):
        self.id = id
        self.name = name


class DummyTransaction(Transaction):
    pass


class DummyTransactionRepo(TransactionRepository[DummyTransaction]):
    def _connect(self):
        return MagicMock(name="MockTransactionConnection")

    def create(self, transaction: DummyTransaction) -> DummyTransaction:
        return transaction

    def read(self, id: int) -> Optional[DummyTransaction]:
        return DummyTransaction()

    def update(
        self, transaction: DummyTransaction
    ) -> Optional[DummyTransaction]:
        return transaction

    def delete(self, id: int) -> Optional[DummyTransaction]:
        return DummyTransaction()

    def search(self, filters: dict) -> List[DummyTransaction]:
        return [DummyTransaction()]

    def search_by_parent(self, entity: HasID) -> List[DummyTransaction]:
        return [DummyTransaction()]

    def all(self) -> List[DummyTransaction]:
        return [DummyTransaction()]


class DummyEntityRepo(EntityRepository[DummyEntity]):
    def _connect(self):
        return MagicMock(name="MockConnection")

    def create(self, entity: DummyEntity) -> DummyEntity:
        entity.id = 1  # simulate DB insert assigning ID
        return entity

    def read(
        self, id: Optional[int] = None, name: Optional[str] = None
    ) -> Optional[DummyEntity]:
        if id == 1 or name == "Test":
            return DummyEntity(1, "Test")
        return None

    def update(self, entity: DummyEntity) -> Optional[DummyEntity]:
        return entity if entity.id == 1 else None

    def delete(self, id: int) -> Optional[DummyEntity]:
        return DummyEntity(id, "Deleted") if id == 1 else None

    def search(self, name_query: str) -> List[DummyEntity]:
        return [DummyEntity(1, "Test")] if "te" in name_query.lower() else []

    def all(self) -> List[DummyEntity]:
        return [DummyEntity(1, "Test"), DummyEntity(2, "Demo")]

    def transaction_repository(
        self, db_path: Optional[Path] = None
    ) -> DummyTransactionRepo:
        return DummyTransactionRepo()

    def get_transactions(self, entity: DummyEntity) -> List[DummyTransaction]:
        return [DummyTransaction()]


class TestDummyEntityRepo(TestCase):
    def setUp(self):
        self.repo = DummyEntityRepo()

    def test_create_sets_id(self):
        entity = DummyEntity(None, "New")
        created = self.repo.create(entity)
        self.assertEqual(created.id, 1)

    def test_read_by_id(self):
        result = self.repo.read(id=1)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Test")

    def test_update_existing(self):
        entity = DummyEntity(1, "Updated")
        updated = self.repo.update(entity)
        self.assertEqual(updated.name, "Updated")

    def test_delete_by_id(self):
        deleted = self.repo.delete(1)
        self.assertEqual(deleted.name, "Deleted")

    def test_search_returns_match(self):
        results = self.repo.search("TE")
        self.assertEqual(len(results), 1)

    def test_all_returns_all_entities(self):
        results = self.repo.all()
        self.assertEqual(len(results), 2)

    def test_transaction_repository_instance(self):
        txn_repo = self.repo.transaction_repository()
        self.assertIsInstance(txn_repo, DummyTransactionRepo)

    def test_get_transactions(self):
        entity = DummyEntity(1, "Test")
        txns = self.repo.get_transactions(entity)
        self.assertTrue(len(txns) > 0)

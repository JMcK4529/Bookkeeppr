from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, List, Optional, TypeVar
from lib.db.transaction import Transaction, TransactionRepository


class Entity(ABC):
    id: Optional[int]
    name: str


T = TypeVar("T", bound=Entity)
U = TypeVar("U", bound=Transaction)
V = TypeVar("V", bound=TransactionRepository)


class EntityRepository(ABC, Generic[T]):
    @abstractmethod
    def _connect(self):
        """Returns a SQLite connection."""
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Creates an entity record in the database."""
        pass

    @abstractmethod
    def read(
        self, id: Optional[int] = None, name: Optional[str] = None
    ) -> Optional[T]:
        """Get an entity by its ID or name, or return None."""
        pass

    @abstractmethod
    def update(self, entity: T) -> Optional[T]:
        """Updates an existing entity record, and propagates the change to corresponding transactions."""
        pass

    @abstractmethod
    def delete(self, id: int) -> Optional[T]:
        """Deletes an existing entity record, and propagates the deletion to corresponding transactions."""
        pass

    @abstractmethod
    def search(self, name_query: str) -> List[T]:
        """Returns a list of entities whose lowercase names have name_query as a substring."""
        pass

    @abstractmethod
    def all(self) -> List[T]:
        """Returns a list of all entities."""
        pass

    @abstractmethod
    def transaction_repository(self, db_path: Optional[Path] = None) -> V:
        """Returns an instance of the repository class for transactions which correspond to the entity type of this class."""
        pass

    @abstractmethod
    def get_transactions(self, entity: T) -> List[U]:
        """Returns a list of transactions corresponding to the given entity."""
        pass

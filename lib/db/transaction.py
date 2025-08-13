from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Protocol, TypeVar


class HasID(Protocol):
    id: int


class Transaction(ABC):
    pass


T = TypeVar("T", bound=Transaction)


class TransactionRepository(ABC, Generic[T]):
    @abstractmethod
    def _connect(self):
        """Returns a SQLite connection."""
        pass

    @abstractmethod
    def create(self, transaction: T) -> T:
        """Creates a transaction record in the database."""
        pass

    @abstractmethod
    def read(self, id: int) -> Optional[T]:
        """Get a transaction by its ID, or return None."""
        pass

    @abstractmethod
    def update(self, transaction: T) -> Optional[T]:
        """Update an existing transaction record."""
        pass

    @abstractmethod
    def delete(self, id: int) -> Optional[T]:
        """Delete an existing transaction record."""
        pass

    @abstractmethod
    def search(self, filters: dict) -> List[T]:
        """Returns a list of transactions matching the supplied filters."""
        pass

    @abstractmethod
    def search_by_parent(self, entity: HasID) -> List[T]:
        """Returns a list of transactions which correspond to the given entity."""
        pass

    @abstractmethod
    def all(self) -> List[T]:
        """Returns a list of all transactions."""
        pass

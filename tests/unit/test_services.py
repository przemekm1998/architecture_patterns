import pytest

from src.allocation.adapters import repository
from src.allocation.adapters.repository import FakeRepository
from src.allocation.domain import model
from src.allocation.domain.model import NotAllocatedOrder
from src.allocation.service_layer import services, unit_of_work


class FakeRepository(repository.AbstractRepository):

    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, sku):
        return next((p for p in self._batches if p.sku == sku), None)

    def list(self):
        return list(self._batches)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):

    def __init__(self):
        self.batches = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("b1", 'COMPLICATED-LAMP', 100, None, uow)
    result = services.allocate("o1", 'COMPLICATED-LAMP', 10, uow)

    assert result == "b1"


def test_error_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch("batch", "EXISTINGSKU", 100, None, uow)
    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTINGSKU"):
        services.allocate("o1", 'NONEXISTINGSKU', 10, uow)


def test_commits():
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "OMINOUS-MIRROR", 100, None, uow)

    services.allocate('o1', 'OMINOUS-MIRROR', 10, uow)
    assert uow.committed is True


def test_deallocate_decrements_available_quantity():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, uow)
    services.allocate('o1', 'BLUE-PLINTH', 10, uow)
    batch = uow.batches.get(sku="BLUE-PLINTH")
    assert batch.available_quantity == 90

    services.deallocate('o1', 'BLUE-PLINTH', 10, uow)
    batch = uow.batches.get(sku='BLUE-PLINTH')
    assert batch.available_quantity == 100


def test_error_for_not_allocated_line():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "AREALSKU", 100, None, uow)

    with pytest.raises(NotAllocatedOrder, match=f"Given order hasn't been allocated"
                                                f" o1"):
        services.deallocate("o1", 'AREALSKU', 10, uow)

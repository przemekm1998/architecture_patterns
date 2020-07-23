import pytest

from src.allocation.adapters.repository import FakeRepository
from src.allocation.domain import model
from src.allocation.domain.model import NotAllocatedOrder
from src.allocation.service_layer import services


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    line = model.OrderLine("o1", 'COMPLICATED-LAMP', 10)
    batch = model.Batch("b1", 'COMPLICATED-LAMP', 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", 'NONEXISTINGSKU', 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTINGSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine('o1', 'OMINOUS-MIRROR', 10)
    batch = model.Batch('b1', 'OMINOUS-MIRROR', 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.committed is True


def test_deallocate_decrements_available_quantity():
    batch = model.Batch('b1', 'BLUE-PLINTH', 100, eta=None)
    order = model.OrderLine('o1', 'BLUE-PLINTH', 10)
    repo = FakeRepository([batch])
    services.allocate(order, repo, FakeSession())
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90

    services.deallocate(order, repo, FakeSession())
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 100


def test_error_for_not_allocated_line():
    line = model.OrderLine("o1", 'AREALSKU', 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(NotAllocatedOrder, match=f"Given order hasn't been allocated"
                                                f" {line.order_id}"):
        services.deallocate(line, repo, FakeSession())

import pytest

from datetime import date, timedelta

from src.allocation.domain.model import Batch, OrderLine, allocate, OutOfStock


@pytest.fixture(scope='module')
def days_after_today():
    def _days_after(days):
        later = date.today() + timedelta(days=days)
        return later

    yield _days_after


@pytest.fixture(scope='module')
def batch_and_line_factory():
    def _make_batch_and_line(sku, batch_qty, line_qty):
        return (
            Batch('batch-001', sku, batch_qty, eta=date.today()),
            OrderLine('order-123', sku, line_qty)
        )

    yield _make_batch_and_line


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch = Batch('batch-001', 'SMALL-TABLE', qty=20, eta=date.today())
    line = OrderLine('order-ref', 'SMALL-TABLE', 2)

    batch.allocate(line)

    assert batch.available_quantity == 18


def test_can_allocate_if_available_grater_than_required(batch_and_line_factory):
    large_batch, small_line = batch_and_line_factory('ELEGANT-LAMP', 20, 2)
    assert large_batch.can_allocate(small_line)


def test_cannot_allocate_if_available_smaller_than_required(batch_and_line_factory):
    small_batch, large_line = batch_and_line_factory('ELEGANT-LAMP', 2, 20)
    assert small_batch.can_allocate(large_line) is False


def test_can_allocate_if_available_equal_to_required(batch_and_line_factory):
    medium_batch, medium_line = batch_and_line_factory('ELEGANT-LAMP', 2, 2)
    assert medium_batch.can_allocate(medium_line)


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch('batch-001', 'NOT-ELEGANT-CHAIR', 100, eta=None)
    different_sku_line = OrderLine('order-123', 'TOSTER', 10)

    assert batch.can_allocate(different_sku_line) is False


def test_deallocate_not_allocated_line_fail(batch_and_line_factory):
    batch, unallocated_line = batch_and_line_factory('DECORATIVE-TRINKET', 20, 2)
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 20


def test_deallocate_allocated_line(batch_and_line_factory):
    batch, allocated_line = batch_and_line_factory('DECORATIVE-TRINKET', 20, 2)
    batch.allocate(allocated_line)
    assert batch.available_quantity == 18

    batch.deallocate(allocated_line)
    assert batch.available_quantity == 20


def test_allocation_is_idempotent(batch_and_line_factory):
    batch, line = batch_and_line_factory('ANGULAR-DESK', 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_prefers_current_stock_batches_to_shipments(days_after_today):
    in_stock = Batch('in-stock-batch', 'RETRO-CLOCK', 100, eta=None)
    shipment_batch = Batch('shipment-batch', 'RETRO-CLOCK', 100,
                           eta=days_after_today(1))
    line = OrderLine('oref', 'RETRO-CLOCK', 10)

    allocate(line, [in_stock, shipment_batch])

    assert in_stock.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches(days_after_today):
    earliest = Batch('speedy-batch', 'MINIMALIST-SPOON', 100, eta=date.today())
    medium = Batch('medium-batch', 'MINIMALIST-SPOON', 100, eta=days_after_today(1))
    latest = Batch('latest-batch', 'MINIMALIST-SPOON', 100, eta=days_after_today(2))

    line = OrderLine('order1', 'MINIMALIST-SPOON', 10)

    allocate(line, [medium, earliest, latest])

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref(days_after_today):
    in_stock_batch = Batch('in-stock-batch-ref', 'HIGHBROW-POSTER', 100, eta=None)
    shipment_batch = Batch('shipment-batch-ref', 'HIGHBROW-POSTER', 100,
                           eta=days_after_today(1))
    line = OrderLine('oref', 'HIGHBROW-POSTER', 10)
    allocation = allocate(line, [in_stock_batch, shipment_batch])

    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch('batch1', 'SMALL-FORK', 10, eta=date.today())
    allocate(OrderLine('order1', 'SMALL-FORK', 10), [batch])

    with pytest.raises(OutOfStock, match='SMALL-FORK'):
        allocate(OrderLine('order2', 'SMALL-FORK', 1), [batch])


def test_prefers_warehouse_batches_to_shipments():
    pytest.fail('todo')


def test_prefers_earlier_batches():
    pytest.fail('todo')

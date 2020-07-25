from datetime import date
from typing import Optional

from src.allocation.adapters.repository import AbstractRepository
from src.allocation.domain import model
from src.allocation.domain.model import OrderLine
from src.allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(ref: str, sku: str, qty: int, eta: Optional[date],
              uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        uow.batches.add(model.Batch(ref, sku, qty, eta))
        uow.commit()


def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> \
        str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f'Invalid sku {line.sku}')
        batchref = model.allocate(line, batches)
        uow.commit()

    return batchref


def deallocate(orderid: str, sku: str, qty: int,
               uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f'Invalid sku {line.sku}')
        batchref = model.deallocate(line, batches)
        uow.commit()
    return batchref


def reallocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) \
        -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        batch = uow.batches.get(sku=line.sku)
        if batch is None:
            raise InvalidSku(f'Invalid sku {line.sku}')
        batch.deallocate(line)
        batches = uow.batches.list()
        batchref = model.allocate(line, batches)
        uow.commit()
    return batchref


def change_batch_quantity(batchref: str, new_qty: int,
                          uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        batch = uow.batches.get(reference=batchref)
        batch.change_purchased_quantity(new_qty)
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
        uow.commit()
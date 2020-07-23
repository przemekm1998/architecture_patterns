import abc

from src.allocation.domain import model


class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class FakeRepository(AbstractRepository):

    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        query = self.session.query(model.Batch).filter_by(reference=reference).one()

        return query

    def list(self):
        return self.session.query(model.Batch).all()


class SqlRepository(AbstractRepository):

    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.execute(
            'INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES '
            ' (:reference, :sku, :purchased_quantity, :eta)',
            dict(reference=batch.reference, sku=batch.sku,
                 purchased_quantity=batch._purchased_quantity,
                 eta=batch.eta)
        )

    def get(self, reference):
        return self.session.execute(
            'SELECT id FROM batches WHERE reference=:reference',
            dict(reference=reference)
        )

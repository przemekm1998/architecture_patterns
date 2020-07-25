import abc

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.allocation import config
from src.allocation.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    batches: repository.AbstractRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(
    config.get_postgres_uri()
))


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):

    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session: Session = self.session_factory()
        self.batches = repository.SqlAlchemyRepository(self.session)

        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    # Automatyczny commit i rollback, lepsze
    # def __exit__(self, exn_type, exn_value, traceback):
    #     if exn_type is None:
    #         self.commit()
    #     else:
    #         self.rollback()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

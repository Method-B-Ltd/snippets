from sqlalchemy import Column, Integer, Boolean
from .base import Base


class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    ...

    @classmethod
    def get_active(cls, session):
        return session.query(cls).filter(cls.archived.is_(False)).all()

    @classmethod
    def get_archived(cls, session):
        return session.query(cls).filter(cls.archived.is_(True)).all()
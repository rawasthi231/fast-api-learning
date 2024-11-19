from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Books(Base):
    __tablename__ = "book"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(50), unique=True)
    author = Column(String(50))
    publisher = Column(String(50))


class Book(BaseModel):
    id: int
    title: str
    author: str
    publisher: str

    class Config:
        from_attributes = True


Base.metadata.create_all(bind=engine)

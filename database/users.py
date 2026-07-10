import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy.orm import DeclarativeBase, relationship
from sqlmodel import Field, SQLModel

class Users(SQLModel, table=True):
    __tablename__ = 'users'

    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4(), primary_key=True)
    first_name: str = Field(index=True, max_length=30)
    last_name: str = Field(index=True, max_length=30)
    email: str = Field(index=True, max_length=45)
    password: str = Field(index=True)
    profile_url: str | None = Field(default=None)

    transactions: ClassVar = relationship("Transactions", back_populates="user")
    budgets: ClassVar = relationship("Budgets", back_populates="user")

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

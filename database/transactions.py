import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
from sqlmodel import Field, SQLModel


class Transactions(SQLModel, table=True):
    __tablename__ = 'transactions'

    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4(), primary_key=True)
    user_id: uuid.UUID = Field(foreign_key='users.id', nullable=False)
    amount: float = Field(index=True)
    date: datetime = Field(index=True)
    recipient: str = Field(index=True, max_length=45)
    category: str = Field(index=True)
    notes: str | None = Field(default=None)
    status: str = Field(default="Pending")
    user: ClassVar = relationship("Users", back_populates="transactions")


    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

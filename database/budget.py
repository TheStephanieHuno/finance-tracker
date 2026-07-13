import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
from sqlmodel import Field, SQLModel


class Budgets(SQLModel, table=True):
    __tablename__ = 'budgets'

    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4(), primary_key=True)
    user_id: uuid.UUID = Field(foreign_key='users.id', nullable=False)
    current_amount: float = Field(index=True)
    target_amount: float = Field(index=True)
    status: str = Field(index=True, max_length=45)
    budget_period: datetime = Field(index=True)

    user: ClassVar = relationship("Users", back_populates="budgets")

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

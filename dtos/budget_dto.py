#to add,delete,update,retrieve
from pydantic import BaseModel
from datetime import datetime

class AddBudget(BaseModel):
    current_amount:float
    target_amount:float
    status:str
    budget_period:datetime

class UpdateBudget(BaseModel):
    current_amount: float
    target_amount: float
    status: str
    budget_period: datetime    
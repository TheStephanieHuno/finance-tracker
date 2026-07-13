# to add,delete,update,retrieve
from pydantic import BaseModel
from datetime import datetime

class AddTransactions(BaseModel):
    amount:float
    date : datetime
    recipient: str
    category : str 
    notes :str
 
class AddTransactionResponse(BaseModel):
    amount:float
    date : datetime
    recipient: str
    category : str 
    notes :str
    
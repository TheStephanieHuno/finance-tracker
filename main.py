from fastapi import FastAPI, Depends
from sqlalchemy import select

from database import Users
from storage.dependencies import get_database

app = FastAPI()


@app.get("/")
async def get_user(db = Depends(get_database)):

    # query statement
    stmt = select(Users).where(Users.id.in_(["3d74d0b33b7e44f2a10aab7474d6bf97"]))

    # execute query
    users = await db.scalars(stmt)
    return {"users": users }


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
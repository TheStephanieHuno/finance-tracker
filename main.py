from fastapi import FastAPI, Depends
from sqlalchemy import select

from database import Users
from dtos.user_dto import RegisterUserResponseDto, RegisterUserRequestDto
from storage.dependencies import get_database

app = FastAPI()


@app.get("/")
async def get_user(db = Depends(get_database)):

    # query statement
    stmt = select(Users).where(Users.id.in_(["3d74d0b33b7e44f2a10aab7474d6bf97"]))

    # execute query
    users = await db.scalars(stmt)
    return {"users": users }


@app.post("/users")
async def create_user(user_dto: RegisterUserRequestDto, db = Depends(get_database)):
    try:
        print("frontend sent user data...", user_dto)

        # Create an instance of the Users model
        user = Users()

        # Assign the data from the frontend to the db user
        user.first_name = user_dto.first_name
        user.last_name = user_dto.last_name
        user.email = user_dto.email
        user.password = user_dto.password

        db.add(user)
        await db.commit()

        user_response = RegisterUserResponseDto(id=str(user.id), email=user.email, first_name=user.first_name, last_name=user.last_name)

        return {"code": 201, "message": "User created successfully", "data": user_response}
    except Exception as e:
        print(e)
        return {"code": 500, "message": "Something went wrong.", "data": None}


@app.get("/users/{id}")
async def get_user_by_id(id: str, db = Depends(get_database)):
    try:
        # query statement
        stmt = select(Users).where(Users.id == id)

        # execute query
        user = await db.scalar(stmt)

        user_response = RegisterUserResponseDto(id=str(user.id), email=user.email, first_name=user.first_name, last_name=user.last_name)

        return {"code": 200, "message": "User fetched successfully", "data": user_response}
    except Exception as e:
        print(e)
        return {"code": 500, "message": "Something went wrong.", "data": None}
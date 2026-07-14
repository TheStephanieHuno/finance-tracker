from fastapi import FastAPI, Depends
from sqlalchemy import select

from database import Users
from database import Transactions
from dtos.user_dto import RegisterUserResponseDto, RegisterUserRequestDto ,LoginUserRequestDto
from dtos.transaction_dto import AddTransactions, AddTransactionResponse
from storage.dependencies import get_database
from pwdlib import PasswordHash
import uuid
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime,timedelta
import jwt
from fastapi import HTTPException
from fastapi import UploadFile, File
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
password_hash = PasswordHash.recommended()

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

#helper function

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=30)

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
   


def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return user_id

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )   

app = FastAPI()


@app.get("/")
async def get_user(token: str = Depends(oauth2_scheme),db = Depends(get_database)):

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

        hashed_password = password_hash.hash(user_dto.password)
        user.password = hashed_password

        db.add(user)
        await db.commit()

        user_response = RegisterUserResponseDto(id=str(user.id), email=user.email, first_name=user.first_name, last_name=user.last_name)

        return {"code": 201, "message": "User created successfully", "data": user_response}
    except Exception as e:
        print(e)
        return {"code": 500, "message": "Something went wrong.", "data": None}


@app.get("/users/{id}")
async def get_user_by_id(id: str,current_user=Depends(get_current_user), db = Depends(get_database)):
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
    
@app.post("/login")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
     db=Depends(get_database)
     ):
    
    try:
        print("User is attempting to log in...")

        # Search for a user whose email OR username matches
        stmt = select(Users).where(
                Users.email == form_data.username,
            
        )

        # Execute the query
        user = await db.scalar(stmt)

        # Check if the user exists
        if user is None:
            return {
                "code": 401,
                "message": "Invalid email or password.",
                "data": None
            }

        # Verifying the entered password against the stored hashed password
        if not password_hash.verify(form_data.password, user.password):
            return {
                "code": 401,
                "message": "Invalid email or password.",
                "data": None
            }

        # Login successful
        token = create_access_token(
    {"sub": str(user.id)}
)

        return {
            "code": 200,
            "message": "Login successful.",
            "data": {
                "id": str(user.id),
                "access_token": token,
                "token_type": "bearer",
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            }
        }

    except Exception as e:
        print(e)
        return {
            "code": 500,
            "message": "Something went wrong.",
            "data": None
        }
    
@app.get("/profile")
async def profile(current_user = Depends(get_current_user)):
    return{"current_user": current_user}


    # Transactions Endpoints 
@app.post("/users/{user_id}/transactions")
async def add_transaction(user_id:str,transaction_dto: AddTransactions, current_user=Depends(get_current_user), db = Depends(get_database)):
    try:
        print("Frontend sent transaction data...", transaction_dto)

        # Create an instance of the Users model
        transaction = Transactions()

        # Assign the data from the frontend to the db user
        transaction.user_id = uuid.UUID(user_id)
        transaction.amount =transaction_dto.amount
        transaction.date =transaction_dto.date
        transaction.recipient =transaction_dto.recipient
        transaction.category =transaction_dto.category
        transaction.notes =transaction_dto.notes
       

        db.add(transaction)
        await db.commit()

        transaction_response = AddTransactionResponse(amount = transaction.amount, date=transaction.date , recipient = transaction.recipient, category = transaction.category , notes=transaction.notes)

        return {"code": 201, "message": "Transaction added successfully", "data": transaction_response}
    except Exception as e:
        print(e)
        return {"code": 500, "message": "Something went wrong.", "data": None}   
    

@app.get("/transactions/{transaction_id}")
async def get_transaction_by_id(transaction_id: str,current_user=Depends(get_current_user), db=Depends(get_database)):
    try:
        stmt = select(Transactions).where(
            Transactions.id == uuid.UUID(transaction_id)
        )

        transaction = await db.scalar(stmt)

        if transaction is None:
            return {
                "code": 404,
                "message": "Transaction not found.",
                "data": None
            }

        return {
            "code": 200,
            "message": "Transaction fetched successfully.",
            "data": transaction
        }

    except Exception as e:
        print(e)

        return {
            "code": 500,
            "message": "Something went wrong.",
            "data": None
        }
    

@app.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    transaction_dto: AddTransactions,
    current_user=Depends(get_current_user),
    db=Depends(get_database)
):
    try:
        stmt = select(Transactions).where(
            Transactions.id == uuid.UUID(transaction_id)
        )

        transaction = await db.scalar(stmt)

        if transaction is None:
            return {
                "code": 404,
                "message": "Transaction not found.",
                "data": None
            }

        transaction.amount = transaction_dto.amount
        transaction.date = transaction_dto.date
        transaction.recipient = transaction_dto.recipient
        transaction.category = transaction_dto.category
        transaction.notes = transaction_dto.notes
        transaction.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(transaction)

        return {
            "code": 200,
            "message": "Transaction updated successfully.",
            "data": transaction
        }

    except Exception as e:
        await db.rollback()
        print(e)

        return {
            "code": 500,
            "message": "Something went wrong.",
            "data": None
        }
@app.post("/users/{user_id}/upload-profile")
async def upload_profile_picture(
    user_id: str,
    file: UploadFile = File(...),
    db=Depends(get_database)
):
    # Create the uploads folder if it doesn't exist
    os.makedirs("uploads", exist_ok=True)

    # Create a unique filename
    filename = f"{user_id}_{file.filename}"

    # Save the file
    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    return {
        "message": "Profile picture uploaded successfully",
        "filename": filename
    }

    
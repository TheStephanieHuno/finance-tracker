from fastapi import FastAPI, Depends
from sqlalchemy import select , text
from database import Users
from database import Transactions
from database import Budgets
from dtos.user_dto import RegisterUserResponseDto, RegisterUserRequestDto ,LoginUserRequestDto,UpdateUserDto
from dtos.transaction_dto import AddTransactions, AddTransactionResponse
from dtos.budget_dto import AddBudget , UpdateBudget
from storage.dependencies import get_database
from pwdlib import PasswordHash
import uuid
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime,timedelta,timezone
import jwt
from fastapi import HTTPException
from fastapi import UploadFile, File
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


security = HTTPBearer()
password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")



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
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

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
                content={
                    "code": 401,
                    "message": "Invalid token",
                    "data": None
                }
            )

        return user_id

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail={
                "code": 401,
                "message": "Invalid token",
                "data": None
            }    
        )  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://finance-tracker-frontend-ebip.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# health check endpoint 
@app.get("/health")
async def health(db=Depends(get_database)):
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))

        return {
            "code": 200,
            "message": "Finance Tracker API is healthy.",
            "data": {
                "status": "healthy",
                "service": "Finance Tracker API",
                "version": "1.0.0",
                "database": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    except Exception as e:
        return {
            "code": 503,
            "message": "Finance Tracker API is unhealthy.",
            "data": {
                "status": "unhealthy",
                "service": "Finance Tracker API",
                "version": "1.0.0",
                "database": "disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        }

# user endpoints
# get all users by id
@app.get("/")
async def get_user(db = Depends(get_database)):

    # query statement
    stmt = select(Users).where(Users.id.in_(["3d74d0b33b7e44f2a10aab7474d6bf97"]))

    # execute query
    users = await db.scalars(stmt)
    return {"users": users }

# create a user
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


# # getting user by id 
# @app.get("/users/{user.id}")
# async def get_user_by_id(id: str,current_user=Depends(get_current_user), db = Depends(get_database)):
#     try:
#         # query statement
#         stmt = select(Users).where(Users.id == id)

#         # execute query
#         user = await db.scalar(stmt)

#         user_response = RegisterUserResponseDto(id=str(user.id), email=user.email, first_name=user.first_name, last_name=user.last_name)

#         return {"code": 200, "message": "User fetched successfully", "data": user_response}
#     except Exception as e:
#         print(e)
#         return {"code": 500, "message": "Something went wrong.", "data": None}
    

# the user is updating /editing his or her details 
@app.patch("/users")
async def update_user(
    update_dto: UpdateUserDto,
    current_user=Depends(get_current_user),
    db=Depends(get_database)
):
    user_id = current_user
    if user_id != current_user:
        raise HTTPException(status_code=403, detail={
            "code": 403,
            "message": "Access denied",
            "data": None
        }
        )

    result = await db.execute(
        select(Users).where(Users.id == current_user)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
              detail={
                "code": 404,
                "message": "User not found",
                "data": None
                    }
                      )

    update_data = update_dto.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return {
        "code":200,
        "message": "User updated successfully",
        "user": user
    }



# the user is deleting the account
@app.delete("/users/me")
async def delete_user(
    current_user=Depends(get_current_user),
    db=Depends(get_database)
):
    
    # Find the logged-in user
    result = await db.execute(
        select(Users).where(Users.id == current_user)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": 404,
                "message": "User not found",
                "data": None
            }
        )

    # Delete the user
    await db.delete(user)
    await db.commit()

    return {
        "code" : 200,
        "message": "User deleted successfully",
        "data": None

    }



# login endpoint 
@app.post("/login")
async def login_user(
    user_dto: LoginUserRequestDto,
    db=Depends(get_database)
):
    try:
        # Find the user by email
        stmt = select(Users).where(
            Users.email == user_dto.email
        )

        user = await db.scalar(stmt)

        # Check if the user exists
        if user is None:
            raise HTTPException(
                status_code=401,
                detail={
                        "code": 401,
                        "message": "Invalid email or password",
                        "data": null
                        }
            )

        # Verify the password
        if not password_hash.verify(
            user_dto.password,
            user.password
        ):
            raise HTTPException(
                status_code=401,
                detail={
                        "code": 401,
                        "message": "Invalid email or password",
                        "data": None
                        }
            )

        # Create the access token
        access_token = create_access_token(
            {
                "sub": str(user.id)
            }
        )

        return {
            "message": "Login successful",
            "code":201,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        print(e)

        raise HTTPException(
            status_code=500,
            detail={
                    "code": 500,
                    "message": "Something went wrong",
                    "data": None
                    }
        )
    


    # Transactions Endpoints
    # adding a transaction 
@app.post("/users/transactions")
async def add_transaction(transaction_dto: AddTransactions, current_user=Depends(get_current_user), db = Depends(get_database)):
    try:
        print("Frontend sent transaction data...", transaction_dto)

        # Create an instance of the Users model
        transaction = Transactions()

        # Assign the data from the frontend to the db user
        user_id = current_user
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
    
# getting a transction by transacation id 
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
    

# getting all transactions by user id and ability to filter and sort
@app.get("/transactions")
async def get_all_transactions(
    current_user=Depends(get_current_user),
    db=Depends(get_database),
    start_date: datetime|None = None,
    end_date: datetime|None = None,
    sort: str = "desc"
):
    query = select(Transactions).where(
        Transactions.user_id == current_user
    )

    # Filter from a specific date
    if start_date:
        query = query.where(Transactions.date >= start_date)

    # Filter up to a specific date
    if end_date:
        query = query.where(Transactions.date <= end_date)

    # Sort by date
    if sort.lower() == "asc":
        query = query.order_by(Transactions.date.asc())
    else:
        query = query.order_by(Transactions.date.desc())

    result = await db.execute(query)
    transactions = result.scalars().all()

    return {
        "code" : 200,
        "message": "Transactions retrieved successfully",
        "count": len(transactions),
        "transactions": transactions
    }

# updating transactions 
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
    
# deleting a transaction 
@app.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_database)
):
    
    # Find the transaction
    result = await db.execute(
        select(Transactions).where(
            Transactions.id == transaction_id
        )
    )

    transaction = result.scalar_one_or_none()

    # Check if transaction exists
    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail={
                    "code": 404,
                    "message": "Transaction NOt found",
                    "data": None
                    }
        )

    # Ensure the transaction belongs to the logged-in user
    if str(transaction.user_id) != str(current_user):
        raise HTTPException(
            status_code=403,
            detail={
                    "code": 403,
                    "message": "You are not authorized to delete this transaction.",
                    "data": None
                    }
        )

    # Delete the transaction
    await db.delete(transaction)
    await db.commit()

    return {
        "code":200,
        "message": "Transaction deleted successfully.",
        "data" : None
    }



# upload profile picture     
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


# budgets endpoints
# addbudget
@app.post("/budgets")
async def add_budget(
    budget_dto: AddBudget,
    current_user=Depends(get_current_user),
    db=Depends(get_database)
):
    try:
        budget = Budgets()
        budget.user_id = uuid.UUID(current_user)
        budget.current_amount = budget_dto.current_amount
        budget.target_amount = budget_dto.target_amount
        budget.status = budget_dto.status
        budget.budget_period = budget_dto.budget_period

        db.add(budget)
        await db.commit()

        return {
            "code":201,
            "message": "Budget created successfully",
            "budget": budget
        }

    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail={
                    "code": 500,
                    "message": "Something went wrong .",
                    "data": None
                    }
        )

# get all budgets by user
@app.get("/budgets")
async def get_all_budgets(
    current_user=Depends(get_current_user),
    db=Depends(get_database)
):
    result = await db.execute(
        select(Budgets).where(
            Budgets.user_id == current_user
        )
    )

    budgets = result.scalars().all()

    return {
        "message": "Budgets retrieved successfully.",
        "count": len(budgets),
        "budgets": budgets
    }




 # update a budget
@app.put("/budgets/{budget_id}")
async def update_budget(
    budget_id: uuid.UUID,
    budget_dto: UpdateBudget,
    current_user=Depends(get_current_user),
    db = Depends(get_database)
):
    result = await db.execute(
        select(Budgets).where(Budgets.id == budget_id)
    )

    budget = result.scalar_one_or_none()

    if budget is None:
        raise HTTPException(
            status_code=404,
            detail={
                    "code": 404,
                    "message": "Budget not found",
                    "data": None
                    }
        )

    # Make sure the budget belongs to the logged-in user
    if budget.user_id != uuid.UUID(current_user):
        raise HTTPException(
            status_code=403,
            detail={
                    "code": 403,
                    "message": "You are not allowed to update this budget.",
                    "data": None
                    }
        )

    budget.current_amount = budget_dto.current_amount
    budget.target_amount = budget_dto.target_amount
    budget.status = budget_dto.status
    budget.budget_period = budget_dto.budget_period

    await db.commit()
   

    return {
        "code":201,
        "message": "Budget updated successfully",
        "budget": budget
    }    



# delete  a budget
@app.delete("/budgets/{budget_id}")
async def delete_budget(
    budget_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_database)
):
    # Find the budget
    result = await db.execute(
        select(Budgets).where(Budgets.id == budget_id)
    )

    budget = result.scalar_one_or_none()

    if budget is None:
        raise HTTPException(
            status_code=404,
            detail={
                    "code": 404,
                    "message": "Budget Not Found.",
                    "data": None
                    }
        )

    # Ensure the budget belongs to the logged-in user
    if str(budget.user_id) != str(current_user):
        raise HTTPException(
            status_code=401,
            detail={
                    "code": 401,
                    "message": "You are not authorized to delete this budget.",
                    "data": None
                    }
        )

    # Delete the budget
    await db.delete(budget)
    await db.commit()

    return {
        "code" : 200,
        "message": "Budget deleted successfully.",
        "data": None
    }
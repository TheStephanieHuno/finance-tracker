from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv
import os
load_dotenv()

sqlalchemy_database_uri = os.getenv("DATABASE_URL")

engine = create_async_engine(sqlalchemy_database_uri, echo=True)

DbContext = async_sessionmaker(bind=engine, expire_on_commit=False)
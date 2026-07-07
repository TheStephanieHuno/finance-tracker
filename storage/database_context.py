from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sqlalchemy_database_uri = "postgresql+psycopg://postgres:postgres@localhost:5432/finance_tracker"

engine = create_async_engine(sqlalchemy_database_uri, echo=True)

DbContext = async_sessionmaker(bind=engine, expire_on_commit=False)
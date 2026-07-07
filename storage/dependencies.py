from storage.database_context import DbContext


async def get_database():
    async with DbContext() as db:
        yield db
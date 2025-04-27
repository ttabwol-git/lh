import os
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

database_url = (
    f"sqlite+aiosqlite:///{os.path.join(os.getenv('DATA_PATH', ''), 'sqldb.db')}"
)
engine = create_async_engine(database_url, future=True, echo=False)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with SessionLocal() as session:
        yield session

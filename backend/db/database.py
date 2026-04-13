from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings


class Base(DeclarativeBase):
    pass


def get_db_url() -> str:
    if settings.POSTGRES_URL:
        return settings.POSTGRES_URL
    return settings.DATABASE_URL


engine = create_async_engine(
    get_db_url(),
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in get_db_url() else {},
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

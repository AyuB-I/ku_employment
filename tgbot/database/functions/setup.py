from typing import Callable

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from tgbot.config import DBConfig


async def create_session_pool(db: DBConfig, echo=False) -> Callable[[], AsyncSession]:
    async_engine = create_async_engine(
        db.construct_sqlalchemy_url(),
        query_cache_size=1200,
        pool_size=20,
        max_overflow=200,
        future=True,
        echo=echo
    )
    session_pool = sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)
    return session_pool

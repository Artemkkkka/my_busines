from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import settings


class DatabaseHelper:
    def __init__(self, url):
        self.engine = create_async_engine(
            url=url,
            # echo=1,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self):
        await self.engine.dispose()

    async def session_getter(self):
        async with self.session_factory() as session:
            yield session


db_helper = DatabaseHelper(
    url=str(settings.db.url),
)

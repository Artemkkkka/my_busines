import asyncio
import os
from typing import Any, Generator

import asyncpg
from alembic import command
from alembic.config import Config
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from src.config import settings
from src.database import db_helper
from src.main import app

CLEAN_TABLES = [
    "meeting",
]


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def run_migrations():
    test_sync_url = settings.db_test.replace("+asyncpg", "")
    prev = os.environ.get("APP_CONFIG__DB__URL")
    os.environ["APP_CONFIG__DB__URL"] = test_sync_url
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield
    if prev is None:
        os.environ.pop("APP_CONFIG__DB__URL", None)
    else:
        os.environ["APP_CONFIG__DB__URL"] = prev


@pytest_asyncio.fixture(scope="session")
async def async_session_test():
    engine = create_async_engine(settings.db_test, future=True, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield async_session
    await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_tables(async_session_test):
    async with async_session_test() as session:
        async with session.begin():
            for table in CLEAN_TABLES:
                await session.execute(
                    text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                )


async def _get_test_db():
    try:
        test_engine = create_async_engine(
            settings.db_test, future=True, echo=True
        )
        test_async_session = sessionmaker(
            test_engine, expire_on_commit=False, class_=AsyncSession
        )
        yield test_async_session()
    finally:
        pass


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, Any, None]:
    app.dependency_overrides[db_helper.session_getter] = _get_test_db
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
async def asyncpg_pool():
    pool = await asyncpg.create_pool(
        "".join(settings.db_test.split("+asyncpg"))
    )
    yield pool
    await pool.close()

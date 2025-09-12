from __future__ import annotations
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config import settings
from src.models.base import Base


config = context.config

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        pass

target_metadata = Base.metadata


def _get_sync_url_from_settings() -> str:
    url = str(settings.db.url)
    if "+aiosqlite" in url:
        return url.replace("+aiosqlite", "")
    if url.startswith("postgresql+asyncpg"):
        return url.replace("+asyncpg", "")
    return url


def run_migrations_offline() -> None:
    url = _get_sync_url_from_settings()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = _get_sync_url_from_settings()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

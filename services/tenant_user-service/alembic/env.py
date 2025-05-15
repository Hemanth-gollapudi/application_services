from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text
from sqlalchemy import MetaData

from alembic import context

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

# Import your SQLAlchemy Base metadata for autogeneration
from tenant_user_service.tenant_management.tenant_lifecycle.realm_management.models import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)  # type: ignore[arg-type]

# Name of the dedicated schema for this service
SCHEMA_NAME = "tenant"

target_metadata: MetaData = Base.metadata

# Postgres role to grant privileges to
POSTGRES_USER = os.getenv("POSTGRES_USER", "appuser")


def get_url() -> str:
    return os.getenv("APP_DATABASE_URL", "postgresql://appuser:changeme@localhost:5432/appdb")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=SCHEMA_NAME,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),  # type: ignore[arg-type]
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=get_url(),
    )

    with connectable.connect() as connection:
        # Create the schema if it doesn't exist
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
        connection.execute(text(f"GRANT ALL PRIVILEGES ON SCHEMA {SCHEMA_NAME} TO \"{POSTGRES_USER}\""))
        connection.commit()  # Commit the schema creation and grant

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=SCHEMA_NAME,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 
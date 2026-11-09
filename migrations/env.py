import os

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from dotenv import load_dotenv

from app.core.database import Base, DATABASE_URL

# Load environment configuration
load_dotenv()

# Import models so SQLAlchemy registers their tables
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.audit_log import AuditLog

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Connect Alembic to SQLAlchemy metadata
target_metadata = Base.metadata

# Use the database URL from .env
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing")

# Escape percent signs for ConfigParser interpolation
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL.replace("%", "%%")
)


def run_migrations_offline() -> None:

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
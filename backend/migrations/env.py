"""Alembic migration environment.

DATABASE_URL is read from the DATABASE_URL environment variable (same as the
app).  The app models are imported so autogenerate can diff against them.
"""
import os
import sys
from pathlib import Path
from logging.config import fileConfig

# Make `app` importable when Alembic is run from the backend/ directory.
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Alembic config object (gives access to alembic.ini values) ───────────────
config = context.config

# Override sqlalchemy.url from the environment so we never hard-code credentials.
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/smart_medi_dev",
)
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target metadata (import ALL models so autogenerate sees every table) ─────
# Import BaseModel first, then every model module so their tables register on
# BaseModel.metadata before Alembic compares against the database.
import app.models  # noqa: F401  — side-effect: registers all tables
from app.models import BaseModel

target_metadata = BaseModel.metadata


# ── Migration runners ─────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """Run migrations without a live database connection (SQL script output)."""
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
    """Run migrations against a live database connection."""
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

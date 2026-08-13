from logging.config import fileConfig

from alembic import context
from pgvector.sqlalchemy import Vector
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

def render_item(type_, obj, autogen_context):
    """Teach autogenerate to emit the pgvector import for Vector columns."""
    if type_ == "type" and isinstance(obj, Vector):
        autogen_context.imports.add("from pgvector.sqlalchemy import Vector")
        return f"Vector(dim={obj.dim})"
    return False  # default rendering for everything else

# Alembic Config object, provides access to the values within the .ini file in use.
config = context.config

# Sets up loggers; Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the app's DATABASE_URL (sync psycopg 3), overriding alembic.ini.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# add model's MetaData object here for 'autogenerate' support: alembic revision --autogenerate
# compare database against SQLAlchemy models
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """
        Run migrations in 'offline' mode.
        Emit SQL without a DB connection (alembic upgrade head --sql).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_item=render_item,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB with a sync engine."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool, # Make the online engine sync; NullPool because a migration connects once and exits; alembic is already sync and to use sync psycopg 3; to confirm it's not the async template.
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

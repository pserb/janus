import logging
from sqlalchemy import inspect
from .database import engine, Base

logger = logging.getLogger("db-initializer")


def init_db():
    """Initialize the database by creating all tables if they don't exist."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    logger.info(f"Existing tables: {existing_tables}")

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Verify tables were created
    tables_to_check = ["companies", "jobs", "sources", "crawl_logs", "sync_info"]
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    logger.info(f"Tables after initialization: {existing_tables}")

    for table in tables_to_check:
        if table not in existing_tables:
            logger.error(f"Table '{table}' was not created!")
        else:
            logger.info(f"Table '{table}' exists")

    return all(table in existing_tables for table in tables_to_check)


if __name__ == "__main__":
    init_db()

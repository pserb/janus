import logging
from sqlalchemy import inspect
from app.database import engine, Base
# Import all models to ensure they're registered with SQLAlchemy
from app.models import Company, Job, Source, CrawlLog, SyncInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('db-init')

# Create tables
logger.info('Creating database tables...')
Base.metadata.create_all(bind=engine)

# Verify tables were created
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
logger.info(f'Tables created: {existing_tables}')

expected_tables = ['companies', 'jobs', 'sources', 'crawl_logs', 'sync_info']
for table in expected_tables:
    if table not in existing_tables:
        logger.error(f'❌ Table {table} is missing!')
    else:
        logger.info(f'✓ Table {table} exists')

success = all(table in existing_tables for table in expected_tables)
print(f'Database initialization {"successful" if success else "failed"}')
print(f'Created tables: {len(existing_tables)}')
print(f'Tables: {", ".join(existing_tables)}')

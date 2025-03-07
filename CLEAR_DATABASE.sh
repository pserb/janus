#!/bin/bash

echo "=== Database Clear Script ==="
echo "WARNING: This will delete all job and company data from the database."
echo "Press CTRL+C now to abort, or Enter to continue..."
read

echo "Creating database reset script..."
cat << 'EOD' > reset_db.py
# reset_db.py
from app.database import SessionLocal, Base, engine
from app.models import Job, Company
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("db-reset")

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    logger.info("Starting database reset")
    
    db = SessionLocal()
    try:
        # Delete all jobs first (due to foreign key constraints)
        logger.info("Deleting all jobs...")
        job_count = db.query(Job).delete()
        db.commit()
        logger.info(f"Deleted {job_count} jobs")
        
        # Delete all companies
        logger.info("Deleting all companies...")
        company_count = db.query(Company).delete()
        db.commit()
        logger.info(f"Deleted {company_count} companies")
        
        logger.info("Database reset complete")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database reset: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
EOD

echo "Copying reset script to backend container..."
docker cp reset_db.py $(docker compose ps -q backend):/app/

echo "Executing database reset..."
docker compose exec backend python reset_db.py

echo "Removing temporary script..."
rm reset_db.py

echo "Database reset complete."
echo "=== Done ==="

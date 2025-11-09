#!/usr/bin/env python3
"""Database migration script to create/update all tables.

This script creates or updates the database schema to match the current models.
For production, consider using Alembic for proper migration management.
"""

import logging
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.database import Base, engine
from backend.app.auth.models import User
from backend.app.tasks.models import Task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def migrate_db() -> None:
    """Create all database tables."""
    logger.info("Starting database migration...")
    logger.info(f"Database engine: {engine.url}")

    try:
        # Import all models to ensure they're registered with Base
        logger.info("Importing models...")
        logger.info(f"  - User: {User.__tablename__}")
        logger.info(f"  - Task: {Task.__tablename__}")

        # Create all tables
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)

        logger.info("✓ Database migration completed successfully")

    except Exception as exc:
        logger.error(f"✗ Database migration failed: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    migrate_db()

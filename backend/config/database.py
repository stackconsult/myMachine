"""
Database Configuration with Connection Pooling
Production-ready database setup for CEP Machine
"""

import os
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import MetaData
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://cep_user:cep_secure_password_2024@localhost:5432/cep_machine"
)

# For SQLite fallback in development
SQLITE_URL = os.getenv(
    "SQLITE_URL",
    "sqlite+aiosqlite:///./data/cep_machine.db"
)

# Use PostgreSQL in production, SQLite in development
def get_database_url() -> str:
    env = os.getenv("PYTHON_ENV", "development")
    if env == "production":
        return DATABASE_URL
    return SQLITE_URL

# Create engine with connection pooling
engine = create_async_engine(
    get_database_url(),
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Session factory
async_session_factory = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get database session with automatic cleanup"""
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        await session.close()

async def init_database():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")

async def close_database():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")

class DatabaseHealth:
    """Database health check utilities"""
    
    @staticmethod
    async def check_connection() -> bool:
        """Check if database connection is healthy"""
        try:
            async with get_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    @staticmethod
    async def get_pool_status() -> dict:
        """Get connection pool status"""
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 0
        }

db_health = DatabaseHealth()

#!/usr/bin/env python3
"""
Database initialization script.
Connects to Postgres and creates the database and tables.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "agent123")
DB_NAME = os.getenv("DATABASE_NAME", "cerina_foundry")


def create_database():
    """Create the database if it doesn't exist."""
    # Connect to default postgres database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'")
    exists = cursor.fetchone()
    
    if not exists:
        logger.info(f"Creating database '{DB_NAME}'...")
        cursor.execute(f'CREATE DATABASE {DB_NAME}')
        logger.info(f"Database '{DB_NAME}' created successfully!")
    else:
        logger.info(f"Database '{DB_NAME}' already exists.")
    
    cursor.close()
    conn.close()


def init_schema():
    """Initialize database schema."""
    logger.info("Initializing database schema...")
    
    # Connect to cerina_foundry database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    # Read and execute schema file
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        
    # Remove the \c command as we're already connected
    schema_sql = schema_sql.replace('\\c cerina_foundry;', '')
    
    cursor.execute(schema_sql)
    conn.commit()
    
    logger.info("Schema initialized successfully!")
    
    cursor.close()
    conn.close()


def main():
    """Main initialization function."""
    try:
        logger.info("Starting database initialization...")
        create_database()
        init_schema()
        logger.info("✅ Database setup completed successfully!")
    except Exception as e:
        logger.error(f"❌ Error during database initialization: {e}")
        raise


if __name__ == "__main__":
    main()

"""
Async-safe PostgreSQL checkpointer for LangGraph.
"""

import os
import asyncio
from typing import Optional
from dotenv import load_dotenv
import logging
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:agent123@postgres-db:5432/cerina_foundry"
)

def _get_safe_url(url: str) -> str:
    if "@" in url:
        parts = url.split("@")
        auth = parts[0].split("//")[1]
        if ":" in auth:
            user = auth.split(":")[0]
            return url.replace(auth, f"{user}:****")
    return url

_global_saver: Optional[AsyncPostgresSaver] = None
_saver_context = None  # Store the context manager for proper cleanup
_init_lock = asyncio.Lock()


async def get_checkpointer_async() -> AsyncPostgresSaver:
    """
    Async-safe initialization for ASGI servers.
    Properly manages the connection pool lifecycle.
    """
    global _global_saver, _saver_context

    if _global_saver is not None:
        return _global_saver

    async with _init_lock:
        if _global_saver is not None:
            return _global_saver

        logger.info(f"🔧 Setting up AsyncPostgresSaver for {_get_safe_url(DATABASE_URL)}")
        
        # Add connection pool parameters to prevent stale connections
        # These parameters enable TCP keepalive to detect dead connections
        # IMPORTANT: autocommit=true is required for DDL statements (CREATE TABLE) to persist
        conn_params = "?keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5&autocommit=true"
        db_url_with_params = DATABASE_URL + conn_params
        
        # Create the context manager with the connection string
        _saver_context = AsyncPostgresSaver.from_conn_string(db_url_with_params)
        
        # Manually enter the context (opens connection pool) but never exit it
        # This keeps the pool alive for the application's lifetime
        saver = await _saver_context.__aenter__()
        
        # Setup the database tables
        logger.info("📋 Creating checkpoint tables...")
        try:
            await saver.setup()
            logger.info("✅ Checkpoint tables created successfully")
        except Exception as e:
            logger.error(f"❌ Error during setup(): {e}", exc_info=True)
            raise
        
        logger.info("✅ AsyncPostgresSaver ready with connection pooling")
        _global_saver = saver
        return _global_saver


def get_checkpointer():
    """
    Return the global saver.
    This MUST NOT run async setup. Lifespan must initialize it first.
    """
    if _global_saver is None:
        raise RuntimeError("Checkpointer not initialized. Call get_checkpointer_async() at startup.")
    return _global_saver


async def reset_checkpointer():
    """Reset the global checkpointer and properly close connections."""
    global _global_saver, _saver_context
    
    if _saver_context is not None:
        try:
            # Properly exit the context manager to close the connection pool
            await _saver_context.__aexit__(None, None, None)
            logger.info("♻️ Connection pool closed")
        except Exception as e:
            logger.warning(f"Error closing connection pool: {e}")
    
    _global_saver = None
    _saver_context = None
    logger.info("♻️ Checkpointer reset")

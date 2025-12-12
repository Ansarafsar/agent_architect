"""
PostgreSQL checkpointer for LangGraph state persistence.
Enables crash recovery and state resumption.
"""
import os
from typing import Optional
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Database connection parameters
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:agent123@localhost:5432/cerina_foundry"
)


class CerinaCheckpointer:
    """
    Wrapper around PostgresSaver with connection management.
    Provides checkpoint persistence for LangGraph workflows.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the checkpointer.
        
        Args:
            connection_string: PostgreSQL connection string. 
                             If None, uses DATABASE_URL from environment.
        """
        self.connection_string = connection_string or DATABASE_URL
        self._pool: Optional[SimpleConnectionPool] = None
        self._saver: Optional[PostgresSaver] = None
        
        logger.info(f"Initializing checkpointer with database: {self._get_safe_url()}")
    
    def _get_safe_url(self) -> str:
        """Get connection URL with password masked for logging."""
        url = self.connection_string
        if "@" in url:
            parts = url.split("@")
            auth_part = parts[0].split("//")[1]
            if ":" in auth_part:
                user = auth_part.split(":")[0]
                return url.replace(auth_part, f"{user}:****")
        return url
    
    def setup(self) -> PostgresSaver:
        """
        Set up the PostgreSQL connection pool and saver.
        
        Returns:
            PostgresSaver instance ready for use with LangGraph
        """
        try:
            # Create connection pool
            self._pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.connection_string
            )
            
            logger.info("Connection pool created successfully")
            
            # Create PostgresSaver from connection string
            self._saver = PostgresSaver.from_conn_string(self.connection_string)
            
            # Initialize checkpoint tables
            self._saver.setup()
            
            logger.info("✅ PostgresSaver initialized and ready")
            
            return self._saver
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize checkpointer: {e}")
            raise
    
    def get_saver(self) -> PostgresSaver:
        """
        Get the PostgresSaver instance.
        
        Returns:
            PostgresSaver instance
            
        Raises:
            RuntimeError: If setup() hasn't been called
        """
        if self._saver is None:
            raise RuntimeError(
                "Checkpointer not initialized. Call setup() first."
            )
        return self._saver
    
    def close(self):
        """Close all connections and cleanup."""
        if self._pool:
            self._pool.closeall()
            logger.info("Connection pool closed")
        
        self._pool = None
        self._saver = None


# Global checkpointer instance
_global_checkpointer: Optional[CerinaCheckpointer] = None


def get_checkpointer(force_new: bool = False) -> CerinaCheckpointer:
    """
    Get the global checkpointer instance.
    
    Args:
        force_new: If True, creates a new instance even if one exists
        
    Returns:
        CerinaCheckpointer instance
    """
    global _global_checkpointer
    
    if _global_checkpointer is None or force_new:
        _global_checkpointer = CerinaCheckpointer()
        _global_checkpointer.setup()
    
    return _global_checkpointer


def reset_checkpointer():
    """Reset the global checkpointer instance."""
    global _global_checkpointer
    
    if _global_checkpointer:
        _global_checkpointer.close()
        _global_checkpointer = None
    
    logger.info("Checkpointer reset")

"""Test script to manually run checkpointer setup and debug issues."""
import asyncio
import os
from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:agent123@postgres-db:5432/cerina_foundry"
)

async def test_setup():
    """Test checkpointer setup."""
    print(f"🔧 Connecting to database...")
    print(f"URL: {DATABASE_URL}")
    
    # Add keepalive parameters
    conn_params = "?keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5"
    db_url_with_params = DATABASE_URL + conn_params
    
    print(f"\n📋 Creating AsyncPostgresSaver...")
    async with AsyncPostgresSaver.from_conn_string(db_url_with_params) as saver:
        print(f"✅ Saver created")
        
        print(f"\n📋 Running setup()...")
        await saver.setup()
        print(f"✅ Setup complete!")
        
        print(f"\n📋 Testing a simple put/get...")
        from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
        
        config = {"configurable": {"thread_id": "test_thread"}}
        checkpoint = Checkpoint(
            v=1,
            id="test_checkpoint_1",
            ts="2024-01-01T00:00:00Z",
            channel_values={"test": "data"},
            channel_versions={},
            versions_seen={}
        )
        metadata = CheckpointMetadata(
            source="test",
            step=1,
            writes={}
        )
        
        await saver.aput(config, checkpoint, metadata, {})
        print(f"✅ Put successful!")
        
        result = await saver.aget_tuple(config)
        print(f"✅ Get successful! Result: {result is not None}")

if __name__ == "__main__":
    asyncio.run(test_setup())

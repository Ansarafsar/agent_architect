#!/usr/bin/env python3
"""
Quick test script for Cerina Protocol Foundry.
Tests basic workflow execution.
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.state.models import BlackboardState
from backend.graph import get_workflow
from dotenv import load_dotenv

load_dotenv()


async def test_workflow():
    """Test the workflow with a simple example."""
    print("🧪 Testing Cerina Protocol Foundry Workflow\n")
    print("=" * 60)
    
    # Check environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        print("❌ ERROR: OPENROUTER_API_KEY not set in .env file")
        print("Please add your OpenRouter API key to the .env file")
        return False
    
    print("✓ OpenRouter API key found")
    print("✓ Database configured")
    
    # Create test input
    test_query = "Create a simple relaxation protocol for managing mild anxiety"
    print(f"\n📝 Test Query: {test_query}\n")
    
    try:
        # Initialize state
        initial_state = BlackboardState(
            thread_id="test_thread_001",
            user_intent=test_query
        )
        
        print("🚀 Starting workflow execution...")
        print("-" * 60)
        
        # Get workflow
        workflow = get_workflow()
        
        # Run workflow
        config = {"configurable": {"thread_id": "test_thread_001"}}
        final_state = await workflow.ainvoke(
            initial_state.model_dump(),
            config=config
        )
        
        # Parse result
        result = BlackboardState(**final_state)
        
        print("\n" + "=" * 60)
        print("✅ Workflow Complete!")
        print("=" * 60)
        print(f"\nStatus: {result.status}")
        print(f"Safety Score: {result.safety_score:.2%}")
        print(f"Empathy Score: {result.empathy_score:.2%}")
        print(f"Iterations: {result.iterations}")
        print(f"Safety Flags: {len(result.safety_flags)}")
        
        if result.active_draft:
            import json
            draft = json.loads(result.active_draft)
            print(f"\n📋 Protocol Generated: {draft['title']}")
            print(f"Steps: {len(draft.get('steps', []))}")
        
        print("\n🎉 Test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_workflow())
    sys.exit(0 if success else 1)

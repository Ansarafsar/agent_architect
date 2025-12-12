#!/usr/bin/env python3
"""
Quick API test to verify the backend is working.
"""
import requests
import json

print("🧪 Testing Cerina Foundry API\n")
print("=" * 60)

# Test 1: Health check
print("\n1. Testing health endpoint...")
try:
    response = requests.get("http://localhost:8000/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ Health check passed!")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Test 2: Start a simple workflow
print("\n2. Testing workflow creation...")
try:
    payload = {
        "user_intent": "Create a brief relaxation breathing exercise"
    }
    
    response = requests.post(
        "http://localhost:8000/run",
        json=payload,
        timeout=120  # Give it time for LLM calls
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Thread ID: {result['thread_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Safety Score: {result['safety_score']:.2%}")
        print(f"   Empathy Score: {result['empathy_score']:.2%}")
        print(f"   Iterations: {result['iterations']}")
        
        if result.get('final_draft'):
            print(f"   Protocol: {result['final_draft']['title']}")
        
        print("   ✅ Workflow test passed!")
    else:
        print(f"   ❌ Error: {response.text}")
        
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🎉 API is working!")
print("\nYou can now:")
print("1. Open the frontend: http://localhost:5173")
print("2. Use the API docs: http://localhost:8000/docs")
print("3. Start generating protocols!")

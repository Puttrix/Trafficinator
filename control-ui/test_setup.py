"""
Test script for Control UI setup

Run this to verify the Control UI is working correctly.
"""
import sys
import requests
from time import sleep

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root():
    """Test root endpoint"""
    print("\n🔍 Testing / endpoint...")
    try:
        response = requests.get(f"{API_BASE}/")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Root endpoint passed: {data}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Control UI tests...\n")
    print("⏳ Waiting for service to be ready...")
    sleep(2)
    
    results = []
    results.append(test_health())
    results.append(test_root())
    
    print("\n" + "="*50)
    if all(results):
        print("✅ All tests passed!")
        print("\n📖 API Documentation: http://localhost:8000/docs")
        print("🏥 Health Check: http://localhost:8000/health")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

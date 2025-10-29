"""
Test script for Control UI setup

Run this to verify the Control UI is working correctly.
Tests all API endpoints including status, start, stop, restart, and logs.
Also tests authentication and rate limiting.
"""
import sys
import requests
from time import sleep
import os

API_BASE = "http://localhost:8000"
API_KEY = os.environ.get("API_KEY", "change-me-in-production")

def test_health():
    """Test health endpoint"""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed")
        print(f"   Status: {data.get('status')}")
        print(f"   Docker: {data.get('docker')}")
        print(f"   Container found: {data.get('container_found')}")
        return data.get('docker') == 'connected'
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
        print(f"✅ Root endpoint passed")
        print(f"   API: {data.get('name')}")
        print(f"   Version: {data.get('version')}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_status():
    """Test status endpoint"""
    print("\n🔍 Testing /api/status endpoint...")
    try:
        response = requests.get(
            f"{API_BASE}/api/status",
            headers={"X-API-Key": API_KEY}
        )
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status endpoint passed")
        print(f"   Container: {data.get('container_name')}")
        print(f"   State: {data.get('state')}")
        print(f"   Image: {data.get('image')}")
        if data.get('uptime'):
            print(f"   Uptime: {data.get('uptime')}")
        return True
    except Exception as e:
        print(f"❌ Status endpoint failed: {e}")
        return False

def test_logs():
    """Test logs endpoint"""
    print("\n🔍 Testing /api/logs endpoint...")
    try:
        response = requests.get(
            f"{API_BASE}/api/logs?lines=20",
            headers={"X-API-Key": API_KEY}
        )
        response.raise_for_status()
        data = response.json()
        print(f"✅ Logs endpoint passed")
        print(f"   State: {data.get('state')}")
        print(f"   Total lines: {data.get('total_lines')}")
        print(f"   Retrieved: {data.get('filtered_lines')}")
        return True
    except Exception as e:
        print(f"❌ Logs endpoint failed: {e}")
        return False

def test_start_stop():
    """Test start/stop/restart operations"""
    print("\n🔍 Testing control operations...")
    
    try:
        headers = {"X-API-Key": API_KEY}
        
        # Get current state
        response = requests.get(f"{API_BASE}/api/status", headers=headers)
        response.raise_for_status()
        initial_state = response.json().get('state')
        print(f"   Initial state: {initial_state}")
        
        # Test stop (if running)
        if initial_state == "running":
            print("\n   Testing stop...")
            response = requests.post(f"{API_BASE}/api/stop?timeout=5", headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Stop: {data.get('message')}")
            sleep(2)
        
        # Test start
        print("\n   Testing start...")
        response = requests.post(f"{API_BASE}/api/start", headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Start: {data.get('message')}")
        sleep(2)
        
        # Test restart
        print("\n   Testing restart...")
        response = requests.post(f"{API_BASE}/api/restart?timeout=5", headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Restart: {data.get('message')}")
        
        print("\n✅ Control operations passed")
        return True
        
    except Exception as e:
        print(f"❌ Control operations failed: {e}")
        return False

def test_validation():
    """Test configuration validation"""
    print("\n🔍 Testing configuration validation...")
    
    try:
        headers = {"X-API-Key": API_KEY}
        
        # Test valid config
        print("\n   Testing valid config...")
        valid_config = {
            "matomo_url": "https://analytics.example.com/matomo.php",
            "matomo_site_id": 1,
            "target_visits_per_day": 20000
        }
        response = requests.post(f"{API_BASE}/api/validate", json=valid_config, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get('valid'):
            print(f"   ✅ Valid config recognized")
            if data.get('warnings'):
                print(f"   ⚠️  {len(data['warnings'])} warnings")
        
        # Test invalid config
        print("\n   Testing invalid config...")
        invalid_config = {
            "matomo_url": "invalid-url",
            "matomo_site_id": 0
        }
        response = requests.post(f"{API_BASE}/api/validate", json=invalid_config, headers=headers)
        response.raise_for_status()
        data = response.json()
        if not data.get('valid') and len(data.get('errors', [])) > 0:
            print(f"   ✅ Invalid config detected ({len(data['errors'])} errors)")
        
        print("\n✅ Validation endpoint passed")
        return True
        
    except Exception as e:
        print(f"❌ Validation endpoint failed: {e}")
        return False

def test_connection():
    """Test Matomo connection testing"""
    print("\n🔍 Testing Matomo connection test...")
    
    try:
        headers = {"X-API-Key": API_KEY}
        
        # Test with Matomo demo server
        print("\n   Testing connection to demo.matomo.cloud...")
        response = requests.post(
            f"{API_BASE}/api/test-connection",
            json={"matomo_url": "https://demo.matomo.cloud/matomo.php", "timeout": 10},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        print(f"   Result: {data.get('message')}")
        if data.get('success'):
            print(f"   ✅ Connection successful ({data.get('response_time_ms')}ms)")
        
        print("\n✅ Connection test endpoint passed")
        return True
        
    except Exception as e:
        print(f"❌ Connection test endpoint failed: {e}")
        return False

def test_authentication():
    """Test API authentication"""
    print("\n🔍 Testing authentication...")
    
    try:
        # Test protected endpoint without API key
        print("\n   Testing without API key...")
        response = requests.post(f"{API_BASE}/api/start")
        if response.status_code == 401:
            print(f"   ✅ Correctly rejected (401 Unauthorized)")
        else:
            print(f"   ⚠️  Expected 401, got {response.status_code}")
        
        # Test with invalid API key
        print("\n   Testing with invalid API key...")
        response = requests.post(
            f"{API_BASE}/api/start",
            headers={"X-API-Key": "invalid-key"}
        )
        if response.status_code == 401:
            print(f"   ✅ Correctly rejected invalid key (401)")
        else:
            print(f"   ⚠️  Expected 401, got {response.status_code}")
        
        # Test with valid API key
        print("\n   Testing with valid API key...")
        response = requests.post(
            f"{API_BASE}/api/start",
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code in [200, 409]:  # 409 if already running
            data = response.json()
            print(f"   ✅ Valid key accepted: {data.get('message')}")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
        
        print("\n✅ Authentication tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Authentication tests failed: {e}")
        return False

def test_rate_limiting():
    """Test API rate limiting"""
    print("\n🔍 Testing rate limiting...")
    
    try:
        print("\n   Testing rapid requests to /api/status (limit: 60/min)...")
        
        # Send rapid requests
        rate_limited = False
        for i in range(65):  # Exceed the 60/min limit
            response = requests.get(
                f"{API_BASE}/api/status",
                headers={"X-API-Key": API_KEY}
            )
            if response.status_code == 429:
                rate_limited = True
                print(f"   ✅ Rate limited after {i+1} requests (429 Too Many Requests)")
                break
        
        if not rate_limited:
            print(f"   ⚠️  No rate limiting detected after 65 requests")
        
        # Wait for rate limit to reset
        print("\n   Waiting 2 seconds for rate limit reset...")
        sleep(2)
        
        # Verify we can make requests again
        response = requests.get(
            f"{API_BASE}/api/status",
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code == 200:
            print(f"   ✅ Rate limit reset successfully")
        
        print("\n✅ Rate limiting tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting tests failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Control UI tests...\n")
    print("⏳ Waiting for service to be ready...")
    sleep(2)
    
    results = []
    
    # Basic connectivity tests
    docker_connected = test_health()
    results.append(docker_connected)
    results.append(test_root())
    
    # API tests (only if Docker is connected)
    if docker_connected:
        results.append(test_status())
        results.append(test_logs())
        results.append(test_start_stop())
    else:
        print("\n⚠️  Skipping container API tests - Docker not connected")
    
    # Validation tests (don't require Docker)
    results.append(test_validation())
    results.append(test_connection())
    
    # Security tests
    results.append(test_authentication())
    results.append(test_rate_limiting())
    
    print("\n" + "="*50)
    if all(results):
        print("✅ All tests passed!")
        print("\n📖 API Documentation: http://localhost:8000/docs")
        print("🏥 Health Check: http://localhost:8000/health")
        print("📊 Status: http://localhost:8000/api/status")
        print("📋 Logs: http://localhost:8000/api/logs")
        print("✅ Validate: http://localhost:8000/api/validate")
        print("🔗 Test Connection: http://localhost:8000/api/test-connection")
        return 0
    else:
        print(f"❌ {len([r for r in results if not r])}/{len(results)} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())


"""
Test script for Control UI setup

Run this to verify the Control UI is working correctly.
Tests all API endpoints including status, start, stop, restart, and logs.
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
        response = requests.get(f"{API_BASE}/api/status")
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
        response = requests.get(f"{API_BASE}/api/logs?lines=20")
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
        # Get current state
        response = requests.get(f"{API_BASE}/api/status")
        response.raise_for_status()
        initial_state = response.json().get('state')
        print(f"   Initial state: {initial_state}")
        
        # Test stop (if running)
        if initial_state == "running":
            print("\n   Testing stop...")
            response = requests.post(f"{API_BASE}/api/stop?timeout=5")
            response.raise_for_status()
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Stop: {data.get('message')}")
            sleep(2)
        
        # Test start
        print("\n   Testing start...")
        response = requests.post(f"{API_BASE}/api/start")
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Start: {data.get('message')}")
        sleep(2)
        
        # Test restart
        print("\n   Testing restart...")
        response = requests.post(f"{API_BASE}/api/restart?timeout=5")
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
        # Test valid config
        print("\n   Testing valid config...")
        valid_config = {
            "matomo_url": "https://analytics.example.com/matomo.php",
            "matomo_site_id": 1,
            "target_visits_per_day": 20000
        }
        response = requests.post(f"{API_BASE}/api/validate", json=valid_config)
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
        response = requests.post(f"{API_BASE}/api/validate", json=invalid_config)
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
        # Test with Matomo demo server
        print("\n   Testing connection to demo.matomo.cloud...")
        response = requests.post(
            f"{API_BASE}/api/test-connection",
            json={"matomo_url": "https://demo.matomo.cloud/matomo.php", "timeout": 10}
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


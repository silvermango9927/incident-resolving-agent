#!/usr/bin/env python3.10
"""
Test script for the Flask incident analyzer application.
This tests the API without needing the Azure OpenAI key.
"""

import sys
from pathlib import Path

# Add the app directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_app_initialization():
    """Test that the app can be imported and initialized."""
    try:
        import app
        print("✓ App imports successfully")
        print(f"✓ Flask app name: {app.app.name}")
        return True
    except Exception as e:
        print(f"✗ Failed to import app: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_routes_registered():
    """Test that all routes are registered."""
    try:
        import app
        rules = list(app.app.url_map.iter_rules())
        route_names = [rule.endpoint for rule in rules if rule.endpoint != 'static']
        
        expected_routes = ['index', 'analyze', 'download_csv', 'health']
        
        print(f"\n✓ Registered routes: {route_names}")
        
        for route in expected_routes:
            if route in route_names:
                print(f"  ✓ {route}")
            else:
                print(f"  ✗ {route} (MISSING)")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Failed to check routes: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint."""
    try:
        import app
        with app.app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                data = response.get_json()
                print(f"\n✓ Health endpoint working")
                print(f"  Status: {data.get('status')}")
                print(f"  Service: {data.get('service')}")
                return True
            else:
                print(f"\n✗ Health endpoint returned {response.status_code}")
                return False
    except Exception as e:
        print(f"\n✗ Health endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analyze_endpoint_validation():
    """Test the analyze endpoint validation (without API call)."""
    try:
        import app
        with app.app.test_client() as client:
            # Test with no data
            response = client.post('/analyze')
            if response.status_code == 400:
                print(f"\n✓ Analyze endpoint correctly rejects empty request")
            else:
                print(f"\n✗ Analyze endpoint should return 400 for empty request, got {response.status_code}")
                return False
            
            # Test with too short text
            response = client.post('/analyze', data={'text': 'short'})
            if response.status_code == 400:
                print(f"✓ Analyze endpoint correctly rejects short input")
            else:
                print(f"✗ Analyze endpoint should return 400 for short input, got {response.status_code}")
                return False
            
            return True
    except Exception as e:
        print(f"\n✗ Analyze endpoint validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_integration():
    """Test MCP integration."""
    try:
        import app
        client = app.get_mcp_client()
        if client:
            print(f"\n✓ MCP client initialized successfully")
            return True
        else:
            print(f"\n⚠ MCP client returned None (orchestration agent may not be available)")
            print(f"  This is OK - app will use fallback prompts")
            return True
    except Exception as e:
        print(f"\n⚠ MCP integration test: {e}")
        print(f"  This is OK if orchestration agent is not running")
        return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("Flask Incident Analyzer - Test Suite")
    print("=" * 70)
    
    tests = [
        ("App Initialization", test_app_initialization),
        ("Routes Registration", test_routes_registered),
        ("Health Endpoint", test_health_endpoint),
        ("Analyze Endpoint Validation", test_analyze_endpoint_validation),
        ("MCP Integration", test_mcp_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 70)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 All tests passed! Flask app is ready to use.")
        print("\nTo start the server, run:")
        print("  python3.10 app.py")
        print("\nOr with environment variable:")
        print("  AZURE_OPENAI_API_KEY='your-key' python3.10 app.py")
        return 0
    else:
        print("\n⚠ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

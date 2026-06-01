#!/usr/bin/env python3
"""
Test script to verify API authentication
"""
import os
import subprocess
import time
import requests
import sys

def run_server_with_env(env_vars):
    """Start server with specific environment variables"""
    env = os.environ.copy()
    env.update(env_vars)

    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    return proc

def test_authentication():
    """Test API authentication in production mode"""
    print("Starting server with ENV=production and API_KEY=test-key-12345...")

    server = run_server_with_env({
        "ENV": "production",
        "API_KEY": "test-key-12345"
    })

    # Give server time to start
    time.sleep(4)

    try:
        base_url = "http://localhost:8000"

        # Test 1: Without X-API-Key (should fail with 422)
        print("\n=== Test 1: /api/stats without X-API-Key ===")
        try:
            response = requests.get(f"{base_url}/api/stats", timeout=5)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 2: With wrong API key (should fail with 403)
        print("\n=== Test 2: /api/stats with wrong X-API-Key ===")
        try:
            response = requests.get(
                f"{base_url}/api/stats",
                headers={"X-API-Key": "wrong-key"},
                timeout=5
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 3: With correct API key (should succeed with 200)
        print("\n=== Test 3: /api/stats with correct X-API-Key ===")
        try:
            response = requests.get(
                f"{base_url}/api/stats",
                headers={"X-API-Key": "test-key-12345"},
                timeout=5
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

        # Get server logs
        print("\n=== Server stderr output (last 20 lines) ===")
        server.terminate()
        stdout, stderr = server.communicate(timeout=5)

        stderr_lines = stderr.decode('utf-8', errors='ignore').split('\n')
        for line in stderr_lines[-20:]:
            if line.strip():
                print(line)

    except Exception as e:
        print(f"Test error: {e}")
        server.kill()
    finally:
        try:
            server.terminate()
            server.wait(timeout=2)
        except:
            server.kill()

if __name__ == "__main__":
    test_authentication()

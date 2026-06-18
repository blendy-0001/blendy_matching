#!/usr/bin/env python
"""
API認証テストスクリプト
本番環境構成(ENV=production)でのテスト
"""
import requests
import time
import os

# 本番環境をシミュレート
os.environ["ENV"] = "production"

BASE_URL = "http://localhost:8000"

def test_api_authentication():
    """API認証の動作確認"""

    print("=" * 60)
    print("API Authentication Test (Production Mode)")
    print("=" * 60)

    # Test 1: /api/stats (認証不要)
    print("\n[Test 1] GET /api/stats (認証不要)")
    try:
        resp = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        if resp.status_code == 200:
            print("[PASS] 200 OK - Public stats endpoint")
        else:
            print(f"[FAIL] Status {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    time.sleep(1)

    # Test 2: POST /api/run-matching without API key
    print("\n[Test 2] POST /api/run-matching without API key")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/run-matching",
            timeout=5,
            json={}
        )
        if resp.status_code == 403:
            print("[PASS] 403 Forbidden - Auth required")
        else:
            print(f"[FAIL] Expected 403, got {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    time.sleep(1)

    # Test 3: POST /api/run-matching with wrong API key
    print("\n[Test 3] POST /api/run-matching with wrong API key")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/run-matching",
            headers={"X-API-Key": "wrong-key"},
            timeout=5,
            json={}
        )
        if resp.status_code == 403:
            print("[PASS] 403 Forbidden - Auth failed")
        else:
            print(f"[FAIL] Expected 403, got {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    time.sleep(1)

    # Test 4: POST /api/run-matching with correct API key
    print("\n[Test 4] POST /api/run-matching with correct API key")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/run-matching",
            headers={"X-API-Key": "dev-api-key-for-testing-local-development"},
            timeout=5,
            json={"max_matches": 5}
        )
        if resp.status_code == 200:
            print("[PASS] 200 OK - Matching started")
            print(f"  Response: {resp.json()}")
        else:
            print(f"[FAIL] Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {e}")

    time.sleep(1)

    # Test 5: GET /docs (認証不要)
    print("\n[Test 5] GET /docs (API Doc - Public)")
    try:
        resp = requests.get(f"{BASE_URL}/docs", timeout=5)
        if resp.status_code == 200:
            print("[PASS] 200 OK - Swagger UI available")
        else:
            print(f"[FAIL] Status {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    test_api_authentication()

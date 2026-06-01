#!/usr/bin/env python
"""Test all API endpoints and verify response structures"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test all endpoints and print results"""

    print("=" * 70)
    print("API ENDPOINT VERIFICATION")
    print("=" * 70)

    # Test 1: GET /api/stats
    print("\n[TEST 1] GET /api/stats")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Fields: success={data.get('success')}, running={data.get('running')}")
        if response.status_code == 200:
            print("[PASS]")
        else:
            print("[FAIL]")
    except Exception as e:
        print(f"[ERROR] {e}")

    # Test 2: GET /api/results
    print("\n[TEST 2] GET /api/results")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/results")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Fields: success={data.get('success')}, running={data.get('running')}, results={data.get('results')}")
        if response.status_code == 200 and isinstance(data, dict) and 'results' in data:
            print("[PASS] Response structure is correct")
        else:
            print("[FAIL]")
    except Exception as e:
        print(f"[ERROR] {e}")

    # Test 3: POST /api/register (valid)
    print("\n[TEST 3] POST /api/register (valid request)")
    print("-" * 70)
    try:
        register_data = {"名前": "Test Company A"}
        response = requests.post(f"{BASE_URL}/api/register", data=register_data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Fields: success={data.get('success')}, page_id={data.get('page_id', 'N/A')[:20]}...")
            print("[PASS]")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"[ERROR] {e}")

    # Test 4: POST /api/register (missing required field)
    print("\n[TEST 4] POST /api/register (missing required field)")
    print("-" * 70)
    try:
        response = requests.post(f"{BASE_URL}/api/register", data={})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 422:
            data = response.json()
            has_detail = 'detail' in data
            print(f"Has error detail: {has_detail}")
            print("[PASS] Returns 422 Validation Error as expected")
        else:
            print(f"[FAIL] Expected 422, got {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    # Test 5: POST /api/run-matching (development mode - no auth required)
    print("\n[TEST 5] POST /api/run-matching (development mode)")
    print("-" * 70)
    try:
        response = requests.post(f"{BASE_URL}/api/run-matching")
        print(f"Status Code: {response.status_code}")
        if response.status_code in [200, 400]:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print("[PASS] Endpoint is accessible")
        else:
            print(f"[FAIL] Status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] {e}")

    # Test 6: Check OpenAPI schema
    print("\n[TEST 6] GET /openapi.json (OpenAPI Schema)")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            schema = response.json()
            title = schema.get('info', {}).get('title', 'N/A')
            version = schema.get('info', {}).get('version', 'N/A')
            endpoints = len(schema.get('paths', {}))
            print(f"API Title: {title}")
            print(f"API Version: {version}")
            print(f"Total Endpoints: {endpoints}")
            print("\nEndpoint List:")
            for path in sorted(schema.get('paths', {}).keys()):
                for method in schema['paths'][path].keys():
                    if method.upper() in ['GET', 'POST']:
                        print(f"  {method.upper()} {path}")
            print("[PASS]")
        else:
            print(f"[FAIL] Status {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    # Test 7: Check /api/run-matching documentation
    print("\n[TEST 7] /api/run-matching Security Documentation")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            schema = response.json()
            run_matching = schema.get('paths', {}).get('/api/run-matching', {}).get('post', {})

            # Check if security is documented
            security = run_matching.get('security', [])
            print(f"Security Requirements: {security if security else 'None (development mode)'}")

            # Check parameters
            parameters = run_matching.get('parameters', [])
            if parameters:
                print("\nParameters documented:")
                for param in parameters:
                    name = param.get('name')
                    required = param.get('required', False)
                    param_in = param.get('in')
                    description = param.get('description', '')
                    print(f"  - {name} (in {param_in}): required={required}")
                    if description:
                        print(f"    Description: {description[:60]}...")

            # Check response schemas
            responses = run_matching.get('responses', {})
            print(f"\nResponse Codes Documented: {', '.join(responses.keys())}")
            print("[PASS]")
        else:
            print(f"[FAIL] Status {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    # Test 8: Check error response models
    print("\n[TEST 8] Error Response Models in OpenAPI")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            schema = response.json()
            components = schema.get('components', {}).get('schemas', {})

            error_models = [k for k in components.keys() if 'Error' in k or 'Response' in k]
            print(f"Response Models Defined: {len(components)}")
            print(f"Error/Response Models: {len(error_models)}")
            if error_models:
                print("\nError Models:")
                for model in sorted(error_models)[:10]:  # Show first 10
                    print(f"  - {model}")
            print("[PASS]")
        else:
            print(f"[FAIL] Status {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_endpoints()

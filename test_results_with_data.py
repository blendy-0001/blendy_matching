#!/usr/bin/env python
"""Test the GET /api/results endpoint with actual data"""
import json

try:
    from fastapi.testclient import TestClient
    from main import app, matching_state
    
    # Initialize client
    client = TestClient(app)
    
    # Set up test data
    print("Setting up test data...")
    matching_state["running"] = False
    matching_state["progress"] = "Test complete"
    matching_state["last_result"] = {
        "matched": [
            {
                "メンバーA名": "ABC Corp",
                "メンバーB名": "XYZ Corp",
                "スコア": 87.5,
                "協業タイプ": "A",
                "マッチング理由": "Similar target clients",
                "紹介文": "Great partnership potential"
            }
        ],
        "unmatched": [
            {
                "名前": "No Match Corp",
                "理由": "Could not find matching pairs meeting criteria"
            }
        ]
    }
    
    # Test the endpoint
    print("\nTesting GET /api/results with data...")
    response = client.get("/api/results")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"OK - Success: {data['success']}")
        print(f"OK - Running: {data['running']}")
        print(f"OK - Progress: {data['progress']}")
        print(f"OK - Results matched count: {len(data['results']['matched'])}")
        print(f"OK - Results unmatched count: {len(data['results']['unmatched'])}")
        print("\nFull response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"FAIL - Error: {response.text}")
    
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()

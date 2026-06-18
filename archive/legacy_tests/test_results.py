#!/usr/bin/env python
"""Test the GET /api/results endpoint"""
import sys
import traceback

try:
    from fastapi.testclient import TestClient
    from main import app, matching_state
    
    # Initialize client
    client = TestClient(app)
    
    # Test the endpoint
    print("Testing GET /api/results...")
    response = client.get("/api/results")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

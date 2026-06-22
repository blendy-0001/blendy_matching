#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug script to inspect app.routes"""
import sys
sys.path.insert(0, '.')

from main import app

print("=" * 70)
print("APP ROUTES DEBUG")
print("=" * 70)

for route in app.routes:
    if hasattr(route, "path") and "/register-multiactivity" in route.path:
        print(f"\nRoute: {route.path}")
        print(f"  Methods: {getattr(route, 'methods', 'N/A')}")
        print(f"  Dir: {[attr for attr in dir(route) if 'openapi' in attr.lower()]}")

        # Check for openapi_extra
        if hasattr(route, "openapi_extra"):
            print(f"  openapi_extra: {route.openapi_extra}")
        else:
            print(f"  openapi_extra: NOT FOUND")

        # Check for operation
        if hasattr(route, "operation"):
            print(f"  operation: {route.operation}")

        # Check other relevant attributes
        for attr in ["endpoint", "response_model", "responses"]:
            if hasattr(route, attr):
                val = getattr(route, attr)
                print(f"  {attr}: {type(val).__name__}")

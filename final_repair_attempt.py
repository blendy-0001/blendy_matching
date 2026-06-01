#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Final attempt to repair Members DB"""
import sys
import os
import requests

sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

# .env ファイル読み込み
env_path = Path(".env")
if env_path.exists():
    with open(env_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
MEMBERS_DB_ID = "517b9ae4-8e9d-496d-b581-927bde2af2fe"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json"
}

print("=" * 70)
print("FINAL REPAIR ATTEMPT: Adding title property to Members DB")
print("=" * 70)
print()

# 最小限のプロパティだけを追加（title）
minimal_props = {
    "名前": {
        "title": {}
    }
}

try:
    url = f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}"

    # Step 1: 現在の状態を確認
    print("Current database state:")
    res = requests.get(url, headers=HEADERS, timeout=5)
    if res.status_code == 200:
        db = res.json()
        print(f"  Properties: {len(db.get('properties', {}))}")
        for prop_name, prop_def in db.get('properties', {}).items():
            print(f"    - {prop_name}")
    else:
        print(f"  Error: {res.status_code}")

    print()
    print("Attempting to add properties...")

    # Step 2: PATCH でプロパティを追加
    res = requests.patch(url, headers=HEADERS, json={"properties": minimal_props}, timeout=5)

    if res.status_code == 200:
        db = res.json()
        print(f"[✓] Success! Properties added.")
        print(f"  New properties: {len(db.get('properties', {}))}")
    else:
        print(f"[✗] Error: {res.status_code}")
        print(f"  Response: {res.json()}")

except Exception as e:
    print(f"[✗] Exception: {e}")

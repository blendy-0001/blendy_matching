#!/usr/bin/env python3
"""検出されたすべてのDBでレコード数をテスト"""
import sys
sys.path.insert(0, '.')

from config import NOTION_API_KEY
import requests

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

# 検出されたDB一覧
databases = {
    "36d2a89c-5c94-809c-835d-000b51099e48": "Members List 2",
    "2e6baab3-4b6c-465d-af11-95e049e2ae9a": "Matching Results",
    "e489e92d-fffc-4ae1-b2d1-0784a57adbfd": "Unmatched Members",
    "4655e4e3-89f0-4852-b999-2801483bd8b5": "Activities",
    "49e6f31e-5bd6-41aa-8cc6-b2d24a61502f": "? (Unknown)"
}

print("=== All Accessible DBs - Record Count Test ===\n")

for db_id, db_name in databases.items():
    try:
        url = f"https://api.notion.com/v1/data_sources/{db_id}/query"
        res = requests.post(url, headers=HEADERS, json={}, timeout=10)

        if res.status_code == 200:
            data = res.json()
            record_count = len(data.get("results", []))
            has_more = data.get("has_more", False)
            status = "OK" if record_count > 0 else "EMPTY"
            print(f"[{status}] {db_id}")
            print(f"      {db_name}")
            print(f"      Records: {record_count}, Has more: {has_more}")
        else:
            print(f"[FAIL] {db_id}")
            print(f"       {db_name}")
            print(f"       Status: {res.status_code}")
            error_msg = res.json().get("message", "Unknown error")
            print(f"       Error: {error_msg[:100]}")
    except Exception as e:
        print(f"[ERROR] {db_id} - {str(e)[:50]}")

    print()

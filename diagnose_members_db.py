"""
メンバーリスト2 の Notion データベースの実際の状態を診断
"""
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
MEMBERS_DB_ID = os.getenv("MEMBERS_DB_ID", "36d2a89c5c948051af07e4db085309dd")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

print(f"MEMBERS_DB_ID = {MEMBERS_DB_ID}")
print(f"NOTION_API_KEY = {NOTION_API_KEY[:20]}...")
print()

# Step 1: データベースメタデータを取得
print("=" * 60)
print("Step 1: Database Metadata")
print("=" * 60)

try:
    db_url = f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}"
    res = requests.get(db_url, headers=HEADERS, timeout=10)
    print(f"GET {db_url}")
    print(f"Status: {res.status_code}")

    if res.status_code == 200:
        db_data = res.json()
        print(f"[OK] Database found: {db_data.get('title', 'No title')}")
        print(f"Icon: {db_data.get('icon')}")
        print(f"Cover: {db_data.get('cover')}")

        # Show properties
        properties = db_data.get("properties", {})
        print(f"\n[PROPERTIES] Database Properties ({len(properties)} total):")
        for prop_name in sorted(properties.keys()):
            prop = properties[prop_name]
            prop_type = prop.get("type", "unknown")
            print(f"  - {prop_name}: {prop_type}")

    else:
        print(f"[ERROR] Error: {res.text}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")

print()

# Step 2: Query でメンバーを取得してみる
print("=" * 60)
print("Step 2: Query Members")
print("=" * 60)

try:
    query_url = f"https://api.notion.com/v1/data_sources/{MEMBERS_DB_ID}/query"
    res = requests.post(query_url, headers=HEADERS, json={}, timeout=10)
    print(f"POST {query_url}")
    print(f"Status: {res.status_code}")

    if res.status_code == 200:
        query_data = res.json()
        results = query_data.get("results", [])
        print(f"[OK] Query successful: {len(results)} members found")

        if results:
            print("\nFirst member:")
            member = results[0]
            print(json.dumps(member, indent=2, ensure_ascii=False)[:1000])
        else:
            print("[WARNING] No members in database")
    else:
        print(f"[ERROR] Query Error: {res.text}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")

print()

# Step 3: ページを作成してみる（テスト）
print("=" * 60)
print("Step 3: Test Page Creation")
print("=" * 60)

try:
    create_url = "https://api.notion.com/v1/pages"
    test_payload = {
        "parent": {"database_id": MEMBERS_DB_ID},
        "properties": {
            "名前": {"title": [{"text": {"content": "テスト_診断用"}}]},
        }
    }
    print(f"POST {create_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2, ensure_ascii=False)}")

    res = requests.post(create_url, headers=HEADERS, json=test_payload, timeout=10)
    print(f"Status: {res.status_code}")

    if res.status_code == 200:
        page_data = res.json()
        page_id = page_data.get("id", "")
        print(f"[OK] Page created successfully!")
        print(f"Page ID: {page_id}")

        # Try to query again
        print("\nQuerying again to see if it appears...")
        query_res = requests.post(query_url, headers=HEADERS, json={}, timeout=10)
        if query_res.status_code == 200:
            updated_results = query_res.json().get("results", [])
            print(f"Total members now: {len(updated_results)}")
    else:
        print(f"[ERROR] Error: {res.text}")
        print(f"Response headers: {dict(res.headers)}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")

print()
print("=" * 60)
print("Diagnosis Complete")
print("=" * 60)

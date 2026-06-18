#!/usr/bin/env python3
"""Test Notion API calls directly"""
import sys
import requests
from config import (
    NOTION_API_KEY,
    MEMBERS_DB_ID,
    ACTIVITIES_DB_ID,
    MEMBERS_DATA_SOURCE_ID,
)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

print("=" * 80)
print("Testing MEMBERS_DB_ID for page creation")
print("=" * 80)
print(f"MEMBERS_DB_ID: {MEMBERS_DB_ID}")

test_payload = {
    "parent": {"database_id": MEMBERS_DB_ID},
    "properties": {
        "名前": {"title": [{"text": {"content": "テスト太郎"}}]},
        "会社名": {"rich_text": [{"text": {"content": "テスト会社"}}]},
    }
}

try:
    res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=test_payload, timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("Testing ACTIVITIES_DB_ID for page creation")
print("=" * 80)
print(f"ACTIVITIES_DB_ID: {ACTIVITIES_DB_ID}")

test_payload = {
    "parent": {"database_id": ACTIVITIES_DB_ID},
    "properties": {
        "アクティビティ名": {"title": [{"text": {"content": "テストアクティビティ"}}]},
    }
}

try:
    res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=test_payload, timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("Testing MEMBERS_DATA_SOURCE_ID for query")
print("=" * 80)
print(f"MEMBERS_DATA_SOURCE_ID: {MEMBERS_DATA_SOURCE_ID}")

test_payload = {
    "filter": {
        "property": "ステータス",
        "select": {"equals": "アクティブ"}
    }
}

try:
    res = requests.post(f"https://api.notion.com/v1/data_sources/{MEMBERS_DATA_SOURCE_ID}/query",
                       headers=HEADERS, json=test_payload, timeout=10)
    print(f"Status: {res.status_code}")
    data = res.json()
    print(f"Total results: {len(data.get('results', []))}")
    if data.get('results'):
        print(f"First result: {data['results'][0]['id']}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("All tests completed")
print("=" * 80)

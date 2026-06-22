#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Find parent page of MEMBERS_DB using Notion Search API"""
import os
import sys
import requests
from pathlib import Path

# Windows PowerShell 文字エンコーディング対応
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .env ファイル読み込み
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
MEMBERS_DB_ID = os.getenv("MEMBERS_DB_ID")

if not NOTION_API_KEY or not MEMBERS_DB_ID:
    print("[ERROR] NOTION_API_KEY or MEMBERS_DB_ID not configured")
    sys.exit(1)

NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json"
}

print("=" * 70)
print("FINDING PARENT PAGE")
print("=" * 70)
print()

# Search for pages containing "メンバーリスト"
print("[1] Searching for pages containing 'メンバーリスト'...")

try:
    res = requests.post(
        f"{NOTION_API_URL}/search",
        headers=HEADERS,
        json={
            "query": "メンバーリスト",
            "filter": {"value": "page", "property": "object"}
        },
        timeout=10
    )
    res.raise_for_status()
    search_results = res.json()
    print(f"[OK] Found {len(search_results.get('results', []))} pages")
except Exception as e:
    print(f"[ERROR] Search failed: {e}")
    sys.exit(1)

print()

# Find the actual parent page
parent_page_ids = []
for page in search_results.get("results", []):
    page_id = page["id"]
    page_title = ""

    if "title" in page:
        page_title = page["title"][0]["plain_text"] if page["title"] else "Untitled"

    print(f"[PAGE] ID: {page_id}")
    print(f"       Title: {page_title}")

    # Check if this is the members database
    if page["object"] == "page":
        parent_page_ids.append((page_id, page_title))

print()
print("=" * 70)
if parent_page_ids:
    print("[SUGGESTION] Potential parent pages found:")
    for i, (pid, title) in enumerate(parent_page_ids, 1):
        print(f"  {i}. {title} ({pid})")
    print()
    print("Use the page ID that contains your member list database.")
else:
    print("[NOTE] No parent pages found via search.")
    print()
    print("Try these alternatives:")
    print("1. Check Notion sidebar - right-click on your database")
    print("2. Look for the database icon and parent page in Notion UI")
    print("3. Use Notion's 'Show in sidebar' to verify the hierarchy")

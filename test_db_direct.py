#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import requests
import json

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
MEMBERS_DB_ID = os.getenv("MEMBERS_DB_ID")

print(f"NOTION_API_KEY: {NOTION_API_KEY[:20]}...")
print(f"MEMBERS_DB_ID: {MEMBERS_DB_ID}")
print()

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

# Step 1: Database スキーマ取得
print("=" * 70)
print("Step 1: Members Database スキーマ取得")
print("=" * 70)

try:
    res = requests.get(
        f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}",
        headers=HEADERS,
        timeout=10
    )
    res.raise_for_status()
    db_schema = res.json()

    props = db_schema.get("properties", {})
    print(f"プロパティ数: {len(props)}")
    print(f"プロパティ一覧:")
    for prop_name, prop_def in props.items():
        prop_type = prop_def.get("type", "unknown")
        print(f"  - {prop_name} ({prop_type})")

except Exception as e:
    print(f"エラー: {e}")
    print()

# Step 2: フィルタなしで全データ取得
print()
print("=" * 70)
print("Step 2: Members DB フィルタなしで全データ取得")
print("=" * 70)

try:
    res = requests.post(
        f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}/query",
        headers=HEADERS,
        json={},  # フィルタなし
        timeout=10
    )
    res.raise_for_status()
    data = res.json()

    results = data.get("results", [])
    print(f"メンバー数: {len(results)}")

    if results:
        first_member = results[0]
        print(f"\n最初のメンバーのプロパティ:")
        for key, value in first_member.get("properties", {}).items():
            print(f"  {key}: {value}")

except Exception as e:
    print(f"エラー: {e}")
    if "res" in locals():
        print(f"Response: {res.text}")

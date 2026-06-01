#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update MEMBERS_DB schema to match form structure"""
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
print("UPDATING MEMBERS DATABASE SCHEMA")
print("=" * 70)
print()

# Step 1: Get current database structure
print("[STEP 1] Getting current database structure...")
try:
    db_id_no_dash = MEMBERS_DB_ID.replace("-", "")
    res = requests.get(
        f"{NOTION_API_URL}/databases/{db_id_no_dash}",
        headers=HEADERS,
        timeout=10
    )
    res.raise_for_status()
    current_db = res.json()
    current_props = current_db.get("properties", {})

    print(f"[OK] Current properties: {len(current_props)}")
    for prop_name in sorted(current_props.keys()):
        prop_type = current_props[prop_name].get("type", "unknown")
        print(f"     - {prop_name} ({prop_type})")
except Exception as e:
    print(f"[ERROR] Failed to get database: {e}")
    sys.exit(1)

print()
print("[STEP 2] Planning schema update...")
print()

# Properties to keep (form fields - basic member info only)
keep_props = {
    "名前",
    "会社名",
    "業種カテゴリ",
    "業種詳細",
    "事業フェーズ",
    "LINE ID",
    "Facebook URL",
    "ステータス"  # Keep status for filtering
}

# New properties to ensure exist (matching form)
new_props = {
    "名前": {"title": {}},
    "会社名": {"rich_text": {}},
    "業種カテゴリ": {
        "select": {
            "options": [
                {"name": "IT・システム開発", "color": "blue"},
                {"name": "コンサルティング", "color": "green"},
                {"name": "マーケティング・営業支援", "color": "yellow"},
                {"name": "ブランディング・デザイン", "color": "purple"},
                {"name": "採用・人材育成", "color": "pink"},
                {"name": "その他", "color": "gray"}
            ]
        }
    },
    "業種詳細": {"rich_text": {}},
    "事業フェーズ": {
        "select": {
            "options": [
                {"name": "プレシード", "color": "blue"},
                {"name": "シード", "color": "green"},
                {"name": "アーリー", "color": "yellow"},
                {"name": "成長期", "color": "purple"},
                {"name": "拡大期", "color": "pink"},
                {"name": "安定期", "color": "gray"}
            ]
        }
    },
    "LINE ID": {"rich_text": {}},
    "Facebook URL": {"url": {}},
    "ステータス": {
        "select": {
            "options": [
                {"name": "アクティブ", "color": "green"},
                {"name": "アーカイブ", "color": "gray"}
            ]
        }
    }
}

# Properties to remove (old activity-related fields)
remove_props = current_props.keys() - keep_props

print(f"Properties to KEEP ({len(keep_props)}):")
for prop_name in sorted(keep_props):
    if prop_name in current_props:
        print(f"  ✓ {prop_name}")

print()
print(f"Properties to REMOVE ({len(remove_props)}):")
for prop_name in sorted(remove_props):
    print(f"  ✗ {prop_name}")

print()

# Step 2: Build DDL statements to remove properties
print("[STEP 3] Building DDL statements...")
ddl_statements = []

# Drop properties to remove
for prop_name in sorted(remove_props):
    ddl_statements.append(f'DROP COLUMN "{prop_name}"')

print(f"[OK] Generated {len(ddl_statements)} DDL statements")
for stmt in ddl_statements[:5]:
    print(f"     {stmt}")
if len(ddl_statements) > 5:
    print(f"     ... and {len(ddl_statements) - 5} more")

print()
print("[STEP 4] Executing schema update...")

if ddl_statements:
    ddl_text = "; ".join(ddl_statements)

    try:
        res = requests.post(
            f"{NOTION_API_URL}/databases/{db_id_no_dash}",
            headers=HEADERS,
            json={
                "properties": {
                    prop_name: prop_def
                    for prop_name, prop_def in new_props.items()
                }
            },
            timeout=10
        )
        res.raise_for_status()
        print("[OK] Schema updated successfully!")

    except Exception as e:
        print(f"[ERROR] Failed to update schema: {e}")
        if "res" in locals():
            print(f"        Response: {res.text[:300]}")
        sys.exit(1)
else:
    print("[INFO] No properties to remove - schema already clean")

print()
print("=" * 70)
print("SUCCESS!")
print("=" * 70)
print()
print("Next steps:")
print("1. Restart the server (Ctrl+C, then: python main.py)")
print("2. Test the form: http://localhost:8000/register-multiactivity")
print()
print("Note: Activity data will be stored in the same Members database")
print("      with a flexible structure (can store 1-3 activities per member)")

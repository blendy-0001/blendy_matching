#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create Activities database using user-provided parent page ID"""
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

print("=" * 70)
print("ACTIVITIES DATABASE CREATION HELPER")
print("=" * 70)
print()

# Get parent page ID from user
print("[1] Find your parent page ID:")
print()
print("    In Notion, navigate to where your member list database is located.")
print("    Right-click on the database → 'Open in new window'")
print("    Look at the URL: https://www.notion.so/[PARENT_PAGE_ID]/...")
print("    Copy the part between 'notion.so/' and the next '/' (with hyphens)")
print()

parent_page_id = input("[INPUT] Enter parent page ID (or 'skip' to use manual setup): ").strip()

if parent_page_id.lower() == 'skip' or not parent_page_id:
    print()
    print("[INFO] Please refer to: setup_activities_db.md")
    print("       For manual database creation instructions.")
    sys.exit(0)

# Format the page ID
parent_page_id = parent_page_id.replace(" ", "")
if len(parent_page_id) == 32 and '-' not in parent_page_id:
    # Add hyphens if needed
    parent_page_id = f"{parent_page_id[:8]}-{parent_page_id[8:12]}-{parent_page_id[12:16]}-{parent_page_id[16:20]}-{parent_page_id[20:]}"

print()
print(f"[INFO] Using parent page ID: {parent_page_id}")
print()

NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json"
}

print("=" * 70)
print("[2] Verifying parent page access...")
print("=" * 70)

try:
    res = requests.get(
        f"{NOTION_API_URL}/pages/{parent_page_id.replace('-', '')}",
        headers=HEADERS,
        timeout=10
    )
    res.raise_for_status()
    parent_page = res.json()
    print("[OK] Parent page confirmed!")
except Exception as e:
    print(f"[ERROR] Cannot access parent page: {e}")
    if "res" in locals():
        print(f"        Response: {res.text[:200]}")
    print()
    print("[HINT] Make sure the page ID is correct and the integration has access.")
    sys.exit(1)

print()
print("=" * 70)
print("[3] Creating Activities database...")
print("=" * 70)

activities_schema = {
    "parent": {
        "type": "page_id",
        "page_id": parent_page_id.replace("-", "")
    },
    "title": [
        {
            "type": "text",
            "text": {
                "content": "Activities"
            }
        }
    ],
    "properties": {
        "アクティビティ名": {
            "title": {}
        },
        "サービス内容": {
            "rich_text": {}
        },
        "対象業界": {
            "rich_text": {}
        },
        "対象企業規模": {
            "select": {
                "options": [
                    {"name": "スタートアップ", "color": "blue"},
                    {"name": "中小企業", "color": "green"},
                    {"name": "中堅企業", "color": "yellow"},
                    {"name": "大企業", "color": "red"}
                ]
            }
        },
        "強み": {
            "multi_select": {
                "options": [
                    {"name": "技術・開発力", "color": "blue"},
                    {"name": "営業・営業ネットワーク", "color": "green"},
                    {"name": "業界知見・実績", "color": "yellow"},
                    {"name": "ブランド・認知度", "color": "purple"},
                    {"name": "コンテンツ・教材", "color": "pink"},
                    {"name": "その他", "color": "gray"}
                ]
            }
        },
        "強み_詳細": {
            "rich_text": {}
        },
        "課題": {
            "multi_select": {
                "options": [
                    {"name": "営業・マーケティング力", "color": "blue"},
                    {"name": "技術・開発力", "color": "green"},
                    {"name": "営業ネットワーク・顧客基盤", "color": "yellow"},
                    {"name": "資金・人材・リソース", "color": "red"},
                    {"name": "業界知見・実績", "color": "purple"},
                    {"name": "その他", "color": "gray"}
                ]
            }
        },
        "課題_詳細": {
            "rich_text": {}
        },
        "ポジション": {
            "multi_select": {
                "options": [
                    {"name": "認知・ブランディング", "color": "blue"},
                    {"name": "集客・マーケティング", "color": "green"},
                    {"name": "リード獲得・見込み客育成", "color": "yellow"},
                    {"name": "営業・提案・クロージング", "color": "red"},
                    {"name": "制作・開発・導入", "color": "purple"},
                    {"name": "運用・保守・継続支援", "color": "pink"},
                    {"name": "教育・研修・人材育成", "color": "orange"},
                    {"name": "経営・戦略・資金調達", "color": "brown"}
                ]
            }
        },
        "Member": {
            "relation": {
                "database_id": MEMBERS_DB_ID.replace("-", "")
            }
        }
    }
}

try:
    res = requests.post(
        f"{NOTION_API_URL}/databases",
        headers=HEADERS,
        json=activities_schema,
        timeout=10
    )
    res.raise_for_status()
    activities_db = res.json()
    activities_db_id = activities_db["id"]

    # Format with hyphens
    formatted_id = f"{activities_db_id[:8]}-{activities_db_id[8:12]}-{activities_db_id[12:16]}-{activities_db_id[16:20]}-{activities_db_id[20:]}"

    print("[OK] Database created successfully!")
    print(f"    ID: {formatted_id}")
except Exception as e:
    print(f"[ERROR] Failed to create database: {e}")
    if "res" in locals():
        print(f"        Response: {res.text[:500]}")
    sys.exit(1)

print()
print("=" * 70)
print("[4] Updating .env file...")
print("=" * 70)

try:
    content = env_path.read_text(encoding="utf-8-sig")

    # Check if ACTIVITIES_DB_ID already exists
    if "ACTIVITIES_DB_ID=" in content:
        # Replace existing line
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("ACTIVITIES_DB_ID="):
                new_lines.append(f'ACTIVITIES_DB_ID="{formatted_id}"')
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        # Add new line
        if not content.endswith("\n"):
            content += "\n"
        content += f'ACTIVITIES_DB_ID="{formatted_id}"\n'

    env_path.write_text(content, encoding="utf-8")
    print("[OK] .env updated!")
    print(f'    ACTIVITIES_DB_ID="{formatted_id}"')
except Exception as e:
    print(f"[ERROR] Failed to update .env: {e}")
    print()
    print("[MANUAL] Add this to .env:")
    print(f'ACTIVITIES_DB_ID="{formatted_id}"')
    sys.exit(1)

print()
print("=" * 70)
print("SUCCESS!")
print("=" * 70)
print()
print("Next steps:")
print("1. Restart the server (Ctrl+C, then python main.py)")
print("2. Test the form: http://localhost:8000/register-multiactivity")
print("3. Verify records in Notion Activities database")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create Activities database under Members database parent page"""
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
print("CREATING ACTIVITIES DATABASE UNDER MEMBERS")
print("=" * 70)
print()

# Step 1: Get MEMBERS_DB parent info
print("[STEP 1] Getting Members database parent page...")
try:
    db_id_no_dash = MEMBERS_DB_ID.replace("-", "")
    res = requests.get(
        f"{NOTION_API_URL}/databases/{db_id_no_dash}",
        headers=HEADERS,
        timeout=10
    )
    res.raise_for_status()
    members_db = res.json()
    parent = members_db["parent"]

    if "block_id" in parent:
        parent_block_id = parent["block_id"]
        # block_id は既にハイフン付きなので、そのまま使用
        parent_page_id = parent_block_id
        print(f"[OK] Parent page found")
        print(f"     Block/Page ID: {parent_page_id}")
    else:
        print(f"[ERROR] Unexpected parent format: {parent}")
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] Failed to get Members DB info: {e}")
    sys.exit(1)

print()

# Step 2: Verify parent page access
print("[STEP 2] Verifying parent page access...")
try:
    res = requests.get(
        f"{NOTION_API_URL}/pages/{parent_page_id.replace('-', '')}",
        headers=HEADERS,
        timeout=10
    )
    if res.status_code == 404:
        print(f"[WARNING] Parent page not directly accessible")
        print(f"          Will attempt database creation anyway...")
    elif res.status_code == 200:
        print(f"[OK] Parent page is accessible")
    else:
        print(f"[WARNING] Unexpected status: {res.status_code}")
except Exception as e:
    print(f"[WARNING] Could not verify parent: {e}")

print()

# Step 3: Create Activities database
print("[STEP 3] Creating Activities database under Members page...")

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
                "database_id": db_id_no_dash
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

    print(f"[OK] Activities database created!")
    print(f"     ID: {formatted_id}")
except Exception as e:
    print(f"[ERROR] Failed to create database: {e}")
    if "res" in locals():
        try:
            error_detail = res.json()
            print(f"       Response: {error_detail.get('message', str(error_detail)[:200])}")
        except:
            print(f"       Response: {res.text[:200]}")
    sys.exit(1)

print()

# Step 4: Update .env
print("[STEP 4] Updating .env file...")
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
        # Add new line after MEMBERS_DB_ID
        if not content.endswith("\n"):
            content += "\n"

        # Find a good place to insert (after MEMBERS_DB_ID)
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.startswith("MEMBERS_DB_ID="):
                new_lines.append(f'ACTIVITIES_DB_ID="{formatted_id}"')
        content = "\n".join(new_lines)

    env_path.write_text(content, encoding="utf-8")
    print(f"[OK] .env updated!")
    print(f'     ACTIVITIES_DB_ID="{formatted_id}"')
except Exception as e:
    print(f"[ERROR] Failed to update .env: {e}")
    print()
    print("[MANUAL] Add this line to .env:")
    print(f'ACTIVITIES_DB_ID="{formatted_id}"')
    sys.exit(1)

print()
print("=" * 70)
print("SUCCESS!")
print("=" * 70)
print()
print("Next steps:")
print("1. Restart the server (Ctrl+C, then: python main.py)")
print("2. Test the form: http://localhost:8000/register-multiactivity")
print("3. Submit a test form and verify the data appears in Notion")
print()
print("The Activities database is now linked to the Members database.")

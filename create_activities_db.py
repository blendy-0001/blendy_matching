#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create Activities database in Notion and update .env"""
import os
import sys
import requests
import json
from pathlib import Path

# Windows PowerShell の出力エンコーディング対応
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .env ファイルのパスを明示的に指定
env_path = Path(__file__).parent / ".env"
print(f"Loading .env from: {env_path}")

# 環境変数を手動で読み込む
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
    print("❌ NOTION_API_KEY または MEMBERS_DB_ID が設定されていません")
    sys.exit(1)

print(f"✓ NOTION_API_KEY: 設定済み")
print(f"✓ MEMBERS_DB_ID: {MEMBERS_DB_ID}")
print()

NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json"
}

print("=" * 70)
print("STEP 1: Get parent page ID from MEMBERS_DB")
print("=" * 70)

# MEMBERS_DB の親ページ ID を取得
try:
    # ID のハイフンを削除してリクエスト
    db_id_no_dash = MEMBERS_DB_ID.replace("-", "")
    res = requests.get(
        f"{NOTION_API_URL}/databases/{db_id_no_dash}",
        headers=HEADERS,
        timeout=10
    )
    res.raise_for_status()
    members_db = res.json()

    # 親の ID を取得（page_id または block_id）
    parent = members_db["parent"]
    if "page_id" in parent:
        parent_id = parent["page_id"]
        parent_type = "page_id"
    else:
        parent_id = parent["block_id"]
        parent_type = "block_id"

    print(f"✓ Parent {parent_type}: {parent_id}")
except Exception as e:
    print(f"❌ Failed to get parent page: {e}")
    if "res" in locals():
        print(f"  Response: {res.text}")
    sys.exit(1)

print()
print("=" * 70)
print("STEP 2: Create Activities database")
print("=" * 70)

# Activities テーブルのスキーマ定義
# 親ページとして block_id をフォーマットして page_id として使用
parent_page_id = parent_id.replace("-", "")
activities_schema = {
    "parent": {
        "type": "page_id",
        "page_id": parent_page_id
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
                "database_id": MEMBERS_DB_ID
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
    print(f"✓ Activities database created successfully!")
    print(f"  ID: {activities_db_id}")
except Exception as e:
    print(f"❌ Failed to create database: {e}")
    if "res" in locals():
        print(f"  Response: {res.text}")
    sys.exit(1)

print()
print("=" * 70)
print("STEP 3: Update .env file")
print("=" * 70)

# .env ファイルに ACTIVITIES_DB_ID を追加
try:
    content = env_path.read_text(encoding="utf-8-sig")

    # 既に存在するかチェック
    if "ACTIVITIES_DB_ID=" in content:
        # 既存行を置換
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("ACTIVITIES_DB_ID="):
                new_lines.append(f'ACTIVITIES_DB_ID="{activities_db_id}"')
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        # 新規行を追加
        if not content.endswith("\n"):
            content += "\n"
        content += f'ACTIVITIES_DB_ID="{activities_db_id}"\n'

    # BOM を保持する場合は utf-8-sig、保持しない場合は utf-8
    env_path.write_text(content, encoding="utf-8")
    print(f"✓ .env file updated successfully!")
    print(f'  ACTIVITIES_DB_ID="{activities_db_id}"')
except Exception as e:
    print(f"❌ Failed to update .env: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("SUCCESS! ✅")
print("=" * 70)
print()
print("次のステップ:")
print("1. サーバーを再起動してください")
print("2. /api/register-multiactivity フォームをテストしてください")
print("3. Notion で Activities データベースに新しいレコードが作成されることを確認してください")

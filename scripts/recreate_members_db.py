#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Recreate Members DB with correct schema"""
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

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json"
}

print("=" * 70)
print("RECREATING MEMBERS DATABASE")
print("=" * 70)
print()

# Step 1: 親ページを取得（from db_response.json）
parent_block_id = "3682a89c-5c94-81d0-b0d2-f6504fe35b99"

# Step 2: 新しいデータベースを作成
print(f"新しいデータベースを親ブロック {parent_block_id} に作成します...")
print()

properties = {
    "名前": {
        "title": {}
    },
    "会社名": {
        "rich_text": {}
    },
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
    "業種詳細": {
        "rich_text": {}
    },
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
    "メール": {
        "email": {}
    },
    "LINE ID": {
        "rich_text": {}
    },
    "Facebook URL": {
        "url": {}
    },
    "ステータス": {
        "select": {
            "options": [
                {"name": "アクティブ", "color": "green"},
                {"name": "アーカイブ", "color": "gray"}
            ]
        }
    }
}

payload = {
    "parent": {
        "type": "workspace"
    },
    "title": [
        {
            "type": "text",
            "text": {
                "content": "👥 メンバーリスト"
            }
        }
    ],
    "description": [
        {
            "type": "text",
            "text": {
                "content": "協業マッチングに申し込んだメンバーの全プロフィール情報"
            }
        }
    ],
    "properties": properties
}

try:
    url = "https://api.notion.com/v1/databases"
    res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    res.raise_for_status()

    new_db = res.json()
    new_db_id = new_db["id"]

    print(f"[✓] 新しいデータベースを作成しました！")
    print(f"    ID: {new_db_id}")
    print(f"    Title: {new_db.get('title', 'N/A')}")
    print(f"    Properties: {len(new_db.get('properties', {}))}")

    print()
    print("=" * 70)
    print("次のステップ:")
    print("=" * 70)
    print(f"1. 古いデータベース ID: 517b9ae4-8e9d-496d-b581-927bde2af2fe")
    print(f"2. 新しいデータベース ID: {new_db_id}")
    print(f"3. .env ファイルの MEMBERS_DB_ID を新しい ID に更新してください")
    print(f"4. サーバーを再起動してください")
    print()

except Exception as e:
    print(f"[✗] エラー: {e}")
    if "res" in locals():
        print(f"    Response: {res.text}")

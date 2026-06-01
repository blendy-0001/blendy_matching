"""
メンバーリスト2 のスキーマを自動作成（data_source ベース）
"""
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
MEMBERS_DB_ID = os.getenv("MEMBERS_DB_ID", "36d2a89c5c948051af07e4db085309dd")
# data_source_id (from notion-fetch result)
DATA_SOURCE_ID = "36d2a89c-5c94-809c-835d-000b51099e48"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

print(f"MEMBERS_DB_ID = {MEMBERS_DB_ID}")
print(f"DATA_SOURCE_ID = {DATA_SOURCE_ID}")
print()

# プロパティの定義
properties = {
    "会社名": {"type": "rich_text"},
    "業種カテゴリ": {
        "type": "select",
        "select": {
            "options": [
                {"name": "SaaS", "color": "blue"},
                {"name": "製造", "color": "orange"},
                {"name": "商社", "color": "green"},
                {"name": "金融", "color": "purple"},
                {"name": "不動産", "color": "red"},
                {"name": "その他", "color": "gray"},
            ]
        }
    },
    "業種詳細": {"type": "rich_text"},
    "事業フェーズ": {
        "type": "select",
        "select": {
            "options": [
                {"name": "プロダクト開発", "color": "yellow"},
                {"name": "成長期", "color": "green"},
                {"name": "安定期", "color": "blue"},
            ]
        }
    },
    "ステータス": {
        "type": "select",
        "select": {
            "options": [
                {"name": "アクティブ", "color": "green"},
                {"name": "アーカイブ", "color": "gray"},
            ]
        }
    },
    "LINE ID": {"type": "rich_text"},
    "Facebook URL": {"type": "url"},
    "アクティビティ数": {"type": "number"},
    "最初のアクティビティ": {"type": "rich_text"},
}

# データベースを更新
print("=" * 60)
print("Updating Database Schema via data_source")
print("=" * 60)

try:
    url = f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}"
    payload = {"properties": properties}

    print(f"PUT {url}")
    print(f"Payload properties ({len(properties)}): {list(properties.keys())}")
    print()

    res = requests.put(url, headers=HEADERS, json=payload, timeout=10)
    print(f"Status: {res.status_code}")

    if res.status_code in [200, 201]:
        print("[OK] Database schema updated successfully!")

        # 更新後のスキーマを確認
        print("\nVerifying schema...")
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            db_data = res.json()
            properties_list = db_data.get("properties", {})
            print(f"[OK] Database now has {len(properties_list)} properties:")
            for prop_name in sorted(properties_list.keys()):
                prop = properties_list[prop_name]
                prop_type = prop.get("type", "unknown")
                print(f"  - {prop_name}: {prop_type}")
    else:
        print(f"[ERROR] Status: {res.status_code}")
        print(f"Response: {res.text[:500]}")

except Exception as e:
    print(f"[ERROR] Exception: {e}")

print()
print("=" * 60)
print("Done")
print("=" * 60)

#!/usr/bin/env python3
"""Notionで現在アクセス可能なすべてのデータベースを検出"""
import sys
sys.path.insert(0, '.')

from config import NOTION_API_KEY
import requests
import json

print("=== Notion アクセス可能データベース検索 ===\n")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

# API キー確認
print("[1] API キー確認")
print(f"[OK] API キー設定: {bool(NOTION_API_KEY)}")
print(f"    キー先頭: {NOTION_API_KEY[:10] if NOTION_API_KEY else 'なし'}...")
print()

# /search エンドポイントで database 型をフィルター
print("[2] /v1/search で全 database を検索")
try:
    url = "https://api.notion.com/v1/search"
    payload = {
        "filter": {
            "value": "data_source",
            "property": "object"
        }
    }

    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    print(f"ステータス: {res.status_code}")

    if res.status_code == 200:
        data = res.json()
        results = data.get("results", [])

        print(f"[SUCCESS] アクセス可能なデータベース数: {len(results)}")
        print()

        if results:
            print("=== 検出されたデータベース一覧 ===")
            for idx, db in enumerate(results, 1):
                db_id = db.get("id", "N/A")
                db_title = db.get("title", [])
                # title は rich_text 配列
                if db_title:
                    title_text = "".join(t.get("plain_text", "") for t in db_title)
                else:
                    title_text = "[No Title]"

                db_icon = db.get("icon") or {}
                if db_icon and db_icon.get("type") == "emoji":
                    icon = db_icon.get("emoji", "")
                else:
                    icon = ""

                print(f"\n[{idx}] {icon} {title_text}")
                print(f"    ID: {db_id}")
                print(f"    Type: {db.get('object', 'N/A')}")
                print(f"    URL: https://app.notion.com/p/{db_id.replace('-', '')}")
        else:
            print("アクセス可能なデータベースが見つかりません")
    else:
        print(f"[ERROR] エラー: {res.status_code}")
        print(f"レスポンス: {res.text[:500]}")

except Exception as e:
    print(f"[ERROR] 例外: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("メンバーリスト用のデータベースを見つけ、")
print(".env の MEMBERS_DB_ID を更新してください")

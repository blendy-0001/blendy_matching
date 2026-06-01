#!/usr/bin/env python3
"""メンバーズDBのスキーマ（プロパティ一覧）を確認"""
import sys
sys.path.insert(0, '.')

from config import NOTION_API_KEY, MEMBERS_DB_ID
import requests
import json

print("=== MEMBERS_DB スキーマ確認 ===\n")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

print(f"[1] データベースID: {MEMBERS_DB_ID}")
print()

# フィルターなしでシンプルなクエリを実行
print("[2] スキーマ取得（最初の1件のみ）")
try:
    url = f"https://api.notion.com/v1/data_sources/{MEMBERS_DB_ID}/query"
    payload = {}

    res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    print(f"ステータス: {res.status_code}")

    if res.status_code == 200:
        data = res.json()
        results = data.get("results", [])

        if results:
            first_record = results[0]
            properties = first_record.get("properties", {})

            print(f"\n[SUCCESS] 最初のレコード取得。プロパティ一覧：")
            print()

            for prop_name, prop_value in properties.items():
                if isinstance(prop_value, dict):
                    prop_type = prop_value.get("type", "unknown")
                    print(f"  - {prop_name} ({prop_type})")

                    # 各プロパティの詳細を表示
                    if prop_type == "rich_text" and prop_value.get("rich_text"):
                        content = "".join(t.get("plain_text", "") for t in prop_value["rich_text"])
                        print(f"      値: {content[:50]}")

                    elif prop_type == "select" and prop_value.get("select"):
                        select_val = prop_value["select"].get("name", "")
                        print(f"      値: {select_val}")

                    elif prop_type == "title" and prop_value.get("title"):
                        content = "".join(t.get("plain_text", "") for t in prop_value["title"])
                        print(f"      値: {content[:50]}")

                    elif prop_type == "url" and prop_value.get("url"):
                        print(f"      値: {prop_value['url'][:50]}")

            print(f"\n[INFO] レコード総数: {len(results)}")
            if data.get("has_more"):
                print(f"[INFO] ページネーション有効（next_cursor 取得可能）")
        else:
            print("[WARNING] レコードが見つかりません")
    else:
        print(f"[ERROR] エラー: {res.status_code}")
        print(f"レスポンス: {res.text[:500]}")

except Exception as e:
    print(f"[ERROR] 例外: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("notion_client.py の get_all_members() 関数のフィルター")
print("をこのスキーマに合わせて修正してください")

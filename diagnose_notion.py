#!/usr/bin/env python3
"""Notion API 接続診断スクリプト"""
import sys
sys.path.insert(0, '.')

from config import NOTION_API_KEY, MEMBERS_DB_ID, MATCHING_HISTORY_DB_ID, MATCHING_RESULTS_DB_ID
import requests

print("=== Notion API 接続診断 ===\n")

# 設定確認
print("[1] 設定確認")
print(f"[OK] API キー設定: {bool(NOTION_API_KEY)}")
print(f"  キー先頭: {NOTION_API_KEY[:10] if NOTION_API_KEY else 'なし'}...")
print(f"[OK] MEMBERS_DB_ID: {MEMBERS_DB_ID}")
print(f"[OK] MATCHING_HISTORY_DB_ID: {MATCHING_HISTORY_DB_ID}")
print(f"[OK] MATCHING_RESULTS_DB_ID: {MATCHING_RESULTS_DB_ID}")
print()

# API 接続テスト
print("\n[2] API 接続テスト")
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

# MEMBERS_DB のテスト
print(f"\n→ {MEMBERS_DB_ID} をクエリ...")
try:
    url = f"https://api.notion.com/v1/data_sources/{MEMBERS_DB_ID}/query"
    payload = {"filter": {"property": "ステータス", "select": {"equals": "アクティブ"}}}

    print(f"   URL: {url}")

    res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    print(f"   ステータス: {res.status_code}")

    if res.status_code == 200:
        data = res.json()
        print(f"   [SUCCESS] 成功！レコード数: {len(data.get('results', []))}")
    else:
        print(f"   [ERROR] エラー：{res.status_code}")
        print(f"   レスポンス: {res.text[:500]}")

except Exception as e:
    print(f"   [ERROR] 例外: {e}")
    import traceback
    traceback.print_exc()

# 他のデータベースもテスト
print(f"\n→ {MATCHING_HISTORY_DB_ID} をクエリ...")
try:
    url = f"https://api.notion.com/v1/data_sources/{MATCHING_HISTORY_DB_ID}/query"
    res = requests.post(url, headers=HEADERS, json={}, timeout=10)
    print(f"   ステータス: {res.status_code}")
    if res.status_code == 200:
        print(f"   [SUCCESS] 成功！")
    else:
        print(f"   [ERROR] エラー：{res.text[:200]}")
except Exception as e:
    print(f"   [ERROR] 例外: {e}")

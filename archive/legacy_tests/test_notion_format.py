#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import requests

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

print(f"元のID: {MEMBERS_DB_ID}")
print(f"Dash削除: {MEMBERS_DB_ID.replace('-', '')}")
print()

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2026-03-11",
}

# パターン1: 元のID（dash含む）
print("パターン1: 元のID（dash含む）")
try:
    url = f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}"
    res = requests.get(url, headers=HEADERS, timeout=5)
    print(f"  URL: {url}")
    print(f"  Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"  ✓ 成功: {len(data.get('properties', {}))} プロパティ")
    else:
        print(f"  ✗ エラー: {res.json().get('message', res.text)}")
except Exception as e:
    print(f"  ✗ 例外: {e}")

print()

# パターン2: Dash削除
print("パターン2: Dash削除")
db_id_no_dash = MEMBERS_DB_ID.replace("-", "")
try:
    url = f"https://api.notion.com/v1/databases/{db_id_no_dash}"
    res = requests.get(url, headers=HEADERS, timeout=5)
    print(f"  URL: {url}")
    print(f"  Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"  ✓ 成功: {len(data.get('properties', {}))} プロパティ")
    else:
        print(f"  ✗ エラー: {res.json().get('message', res.text)}")
except Exception as e:
    print(f"  ✗ 例外: {e}")

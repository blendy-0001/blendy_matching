#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Repair Members DB schema"""
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
MEMBERS_DB_ID = os.getenv("MEMBERS_DB_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json"
}

print("=" * 70)
print("REPAIRING MEMBERS DATABASE SCHEMA")
print("=" * 70)
print()

# 修復対象のプロパティ定義
properties_to_create = {
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

print(f"修復対象プロパティ数: {len(properties_to_create)}")
for prop_name in sorted(properties_to_create.keys()):
    print(f"  - {prop_name}")

print()
print("プロパティを追加します...")
print()

try:
    url = f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}"
    payload = {
        "properties": properties_to_create
    }

    res = requests.patch(url, headers=HEADERS, json=payload, timeout=10)
    res.raise_for_status()

    print(f"[✓] スキーマ修復成功！")
    result = res.json()
    new_props = result.get("properties", {})
    print(f"    追加されたプロパティ数: {len(new_props)}")
    for prop_name in sorted(new_props.keys()):
        prop_type = new_props[prop_name].get("type", "unknown")
        print(f"      - {prop_name} ({prop_type})")

except Exception as e:
    print(f"[✗] エラー: {e}")
    if "res" in locals():
        print(f"    Response: {res.text}")

print()
print("=" * 70)
print("修復完了！サーバーを再起動してください。")
print("=" * 70)

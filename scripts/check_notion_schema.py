"""Notion API スキーマ確認スクリプト"""
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
MEMBERS_DB_ID = os.getenv("MEMBERS_DB_ID")
ACTIVITIES_DB_ID = os.getenv("ACTIVITIES_DB_ID")
MATCHING_HISTORY_DB_ID = os.getenv("MATCHING_HISTORY_DB_ID")
MATCHING_RESULTS_DB_ID = os.getenv("MATCHING_RESULTS_DB_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

print("=" * 80)
print("NOTION API スキーマ確認（2026-05-28）")
print("=" * 80)

def get_db_schema(db_id, db_name):
    """DB のスキーマを取得"""
    url = f"https://api.notion.com/v1/databases/{db_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()

        print(f"\n📋 {db_name}")
        print(f"   ID: {db_id}")
        prop_count = len(data.get('properties', {}))
        print(f"   プロパティ数: {prop_count}")

        if prop_count == 0:
            print("   ⚠️  プロパティが 0 個（Notion free plan ブロック制限の可能性）")
            return False

        print("   プロパティ一覧（最初の 15 個）:")
        for i, (prop_name, prop_data) in enumerate(list(data.get('properties', {}).items())[:15]):
            prop_type = prop_data.get('type')
            print(f"      {i+1:2}. {prop_name:25} ({prop_type})")

        return True
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False

# 各 DB のスキーマを確認
results = {}
results['members'] = get_db_schema(MEMBERS_DB_ID, "📥 Members DB（メンバーリスト）")
results['activities'] = get_db_schema(ACTIVITIES_DB_ID, "🎯 Activities DB（事業アクティビティ）")
results['history'] = get_db_schema(MATCHING_HISTORY_DB_ID, "🔗 Matching History DB")
results['results'] = get_db_schema(MATCHING_RESULTS_DB_ID, "📋 Matching Results DB")

print("\n" + "=" * 80)
print("検査結果サマリー")
print("=" * 80)
if all(results.values()):
    print("✅ 全 DB のスキーマが正常です（Notion Business プランのアップグレード確認）")
else:
    failed = [k for k, v in results.items() if not v]
    print(f"❌ {', '.join(failed)} で問題が検出されました")
    print("   → Notion Business プランへのアップグレードを確認してください")

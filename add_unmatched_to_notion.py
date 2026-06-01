"""
繋いでない16名を Notion に「マッチング待ち」として追加
"""
import sys
import io
import json
import requests
from config import NOTION_API_KEY, MATCHING_RESULTS_DB_ID
from datetime import datetime

# UTF-8エンコーディング対応
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# 繋いでない16名
unmatched_members = [
    "テスト07", "テスト08", "テスト14", "テスト16", "テスト17",
    "テスト37", "テスト47",
    "中村光太", "伊藤健一", "佐藤次郎", "吉田拓也", "小島結衣",
    "山田太郎", "渡辺由美", "田中美咲", "鈴木花子"
]

print("\n" + "="*70)
print("[ADD] 繋いでない16名を Notion に「マッチング待ち」として追加中...")
print("="*70 + "\n")

session_name = f"{datetime.now().strftime('%Y年%m月')} 第{'1回' if datetime.now().day <= 15 else '2回'}"
added = 0
failed = 0

for name in unmatched_members:
    try:
        # Notion ページ作成
        url = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": MATCHING_RESULTS_DB_ID},
            "properties": {
                "セッション名": {
                    "title": [{"text": {"content": session_name}}]
                },
                "メンバーA名": {
                    "rich_text": [{"text": {"content": name}}]
                },
                "メンバーB名": {
                    "rich_text": [{"text": {"content": "🔄 マッチング相手を探索中"}}]
                },
                "協業タイプ": {
                    "select": {"name": "⏳ 手動対応待ち"}
                },
                "スコア": {
                    "number": None
                },
                "マッチング理由": {
                    "rich_text": [{"text": {"content": "外部リストから相手を見つけ中"}}]
                },
                "紹介文": {
                    "rich_text": [{"text": {"content": "[未対応] このメンバーのマッチング相手を手動で探して追加してください"}}]
                },
                "実施日": {
                    "date": {"start": datetime.now().strftime("%Y-%m-%d")}
                },
                "ステータス": {
                    "select": {"name": "保留中"}
                }
            }
        }

        response = requests.post(url, headers=HEADERS, json=payload)
        if response.status_code == 200:
            added += 1
            print(f"  ✅ {name} を追加しました")
        else:
            failed += 1
            print(f"  ❌ {name} 追加失敗: {response.status_code}")
            print(f"     {response.text}")

    except Exception as e:
        failed += 1
        print(f"  ❌ {name} 追加エラー: {e}")

print("\n" + "="*70)
print(f"[DONE] {added}名を追加しました（失敗: {failed}名）")
print("="*70)
print("\n💡 Notion で確認:")
print(f"   https://www.notion.so/.../{MATCHING_RESULTS_DB_ID}")
print("   → 「ステータス」「協業タイプ」で「手動対応待ち」フィルタで表示\n")

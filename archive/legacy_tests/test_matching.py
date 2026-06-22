"""
マッチングエンジンの直接テスト
"""
import json
import sys
from notion_client import get_all_members, get_matched_pairs, save_matching_result, save_to_history
from matching_engine import run_matching
from datetime import datetime

# UTF-8エンコーディング設定
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*60)
print("[TEST] 協業マッチングシステム テスト実行")
print("="*60)

# Step 1: メンバー取得
print("\n[STEP 1] メンバーリストを読み込み中...")
members = get_all_members()
print(f"[OK] {len(members)}名のメンバーを取得しました")

if not members:
    print("[ERROR] メンバーがいません。create_test_data.py で登録してください")
    exit(1)

# メンバーサマリー表示
print("\n[MEMBERS] メンバーリスト:")
for i, m in enumerate(members, 1):
    print(f"  {i}. {m.get('名前', 'N/A')} ({m.get('会社名', 'N/A')})")

# Step 2: マッチング履歴取得
print("\n[STEP 2] マッチング履歴を確認中...")
matched_pairs = get_matched_pairs()
print(f"[OK] {len(matched_pairs)}組のマッチング履歴を取得しました")

# Step 3: マッチング実行
print("\n[STEP 3] ルールベースマッチングを実行中...")
results = run_matching(members, matched_pairs)

if not results:
    print("[WARN] マッチング可能なペアが見つかりませんでした")
    exit(0)

print(f"[OK] {len(results)}組のマッチングが完了しました\n")

# Step 4: 結果表示
print("[RESULTS] マッチング結果:\n")
for i, match in enumerate(results, 1):
    print(f"--- マッチング {i} ---")
    print(f"  メンバーA: {match['メンバーA名']}")
    print(f"  メンバーB: {match['メンバーB名']}")
    print(f"  スコア: {match['スコア']}")
    print(f"  協業タイプ: {match['協業タイプ']}")
    print(f"  マッチング理由: {match['マッチング理由']}")
    intro_preview = match['紹介文'][:80] if len(match['紹介文']) > 80 else match['紹介文']
    print(f"  紹介文: {intro_preview}...")
    print()

# Step 5: Notionに保存
print("[STEP 4] 結果をNotionに保存中...")
session_name = f"{datetime.now().strftime('%Y年%m月')} 第{'1回' if datetime.now().day <= 15 else '2回'}"

saved_count = 0
for match in results:
    try:
        save_matching_result(session_name, match)
        save_to_history(match)
        saved_count += 1
    except Exception as e:
        print(f"  [WARN] {match['メンバーA名']} × {match['メンバーB名']}: {e}")

print(f"[OK] {saved_count}組をNotionに保存しました")

print("\n" + "="*60)
print("[DONE] テスト完了！")
print("="*60 + "\n")

"""
最新のマッチング結果から「繋いでない人」を見つける
"""
import sys
import io
from notion_client import get_all_members, get_matching_results

# UTF-8エンコーディング対応
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*60)
print("[SEARCH] 繋いでない人を探索中...")
print("="*60)

# Step 1: メンバー取得
print("\n[STEP 1] メンバーを取得中...")
members = get_all_members()
all_member_names = {m["名前"] for m in members}
print(f"[OK] {len(members)}名のメンバーを取得しました")

# Step 2: 最新のマッチング結果を取得
print("\n[STEP 2] 最新のマッチング結果を確認中...")
matched_results = get_matching_results()
print(f"[OK] {len(matched_results)}組のマッチング結果を取得しました")

# Step 3: マッチングされたメンバーを抽出
matched_members = set()
for match in matched_results:
    a_name = match.get("メンバーA名") or match.get("properties", {}).get("メンバーA名", {}).get("title", [])
    b_name = match.get("メンバーB名") or match.get("properties", {}).get("メンバーB名", {}).get("title", [])

    # 両方のフォーマットに対応
    if isinstance(a_name, list):
        a_name = a_name[0] if a_name else None
    if isinstance(b_name, list):
        b_name = b_name[0] if b_name else None

    if a_name:
        matched_members.add(a_name)
    if b_name:
        matched_members.add(b_name)

print(f"\n[MATCHED] マッチング済みメンバー: {len(matched_members)}名")
for i, name in enumerate(sorted(matched_members), 1):
    print(f"  {i}. {name}")

# Step 4: 繋いでないメンバーを見つける
unmatched = all_member_names - matched_members
unmatched_list = sorted(unmatched)

print(f"\n[UNMATCHED] 繋いでない人（手動で探すべきメンバー）: {len(unmatched_list)}名\n")
for i, name in enumerate(unmatched_list, 1):
    print(f"  {i}. {name}")

# Step 5: 最高スコアの候補ペアを探す（参考用）
print(f"\n[TIPS] これらのメンバーを外部リストから見つけて、Notion に追加してください！")
print("="*60 + "\n")

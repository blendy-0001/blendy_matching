"""
残り3件のマッチング候補を見つける
- スコア45未満で除外されたペア
- 現在マッチングされていないメンバー
"""
import sys
import io
import itertools
from notion_client import get_all_members, get_matched_pairs
from matching_engine import _score_pair_rules

# UTF-8エンコーディング対応
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*60)
print("[SEARCH] 残り3件のマッチング候補を探索中...")
print("="*60)

# Step 1: メンバー取得
print("\n[STEP 1] メンバーを取得中...")
members = get_all_members()
print(f"[OK] {len(members)}名のメンバーを取得しました")

# Step 2: マッチング履歴取得
print("\n[STEP 2] マッチング履歴を確認中...")
matched_pairs = get_matched_pairs()
print(f"[OK] {len(matched_pairs)}組のマッチング履歴を取得しました")

# Step 3: 有効なペアを生成
print("\n[STEP 3] すべてのペアをスコアリング中...")
valid_pairs = []
all_scores = []

for a, b in itertools.combinations(members, 2):
    pair_key = frozenset([a["名前"], b["名前"]])
    if pair_key not in matched_pairs:
        valid_pairs.append((a, b))

print(f"  → {len(valid_pairs)}組をスコアリング...")

for a, b in valid_pairs:
    result = _score_pair_rules(a, b)
    if result:
        all_scores.append(result)

# スコア降順でソート
all_scores.sort(key=lambda x: x["スコア"], reverse=True)

# Step 4: 除外されたペアを抽出
print("\n[EXCLUDED] スコア45未満で除外されたペア（上位10件）:\n")
excluded = [s for s in all_scores if s["スコア"] < 45]
for i, match in enumerate(excluded[:10], 1):
    print(f"{i}. {match['メンバーA名']} × {match['メンバーB名']} (スコア: {match['スコア']})")
    print(f"   理由: {match['マッチング理由']}")
    print()

# Step 5: 現在マッチング済みのメンバーをリストアップ
print("\n[MATCHED] 現在マッチング済みのメンバー:\n")
matched_members = set()
for match_history in matched_pairs:
    matched_members.add(list(match_history)[0])
    matched_members.add(list(match_history)[1])

matched_list = sorted(matched_members)
for i, name in enumerate(matched_list, 1):
    print(f"{i}. {name}")

# Step 6: マッチングされていないメンバー
print("\n[UNMATCHED] マッチングされていないメンバー:\n")
all_members = {m["名前"] for m in members}
unmatched = all_members - matched_members
unmatched_list = sorted(unmatched)
for i, name in enumerate(unmatched_list, 1):
    print(f"{i}. {name}")

# Step 7: 推奨候補（スコア35以上45未満）
print("\n[RECOMMENDATION] 推奨マッチング候補（スコア35～44）:\n")
candidates = [s for s in all_scores if 35 <= s["スコア"] < 45]
candidates_sorted = candidates[:15]  # 上位15件

for i, match in enumerate(candidates_sorted, 1):
    a_name = match['メンバーA名']
    b_name = match['メンバーB名']
    a_matched = a_name in matched_members
    b_matched = b_name in matched_members

    status = ""
    if not a_matched and not b_matched:
        status = "✅ 両方未マッチ（おすすめ！）"
    elif not a_matched or not b_matched:
        status = "△ どちらか未マッチ"
    else:
        status = "⚠️  両方既マッチ（避けるべき）"

    print(f"{i}. {a_name} × {b_name}")
    print(f"   スコア: {match['スコア']} | {status}")
    print(f"   協業タイプ: {match['協業タイプ']}")
    print(f"   理由: {match['マッチング理由']}")
    print()

print("="*60)
print("[DONE] 探索完了！\n")
print("💡 推奨: 上記の「✅ 両方未マッチ」から3件を選んでください")
print("="*60 + "\n")

"""マッチング済みメンバーの分析"""
import sys
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from notion_client import get_all_members, get_matched_pairs

print("\n" + "="*60)
print("[ANALYSIS] マッチング済みメンバー分析")
print("="*60 + "\n")

# メンバー取得
members = get_all_members()
member_names = {m.get('名前', 'N/A') for m in members}

print(f"[TOTAL] メンバー総数: {len(members)}名")
print(f"[MEMBERS] {', '.join(sorted(member_names))}\n")

# マッチング履歴取得
matched_pairs = get_matched_pairs()
print(f"[HISTORY] マッチング履歴: {len(matched_pairs)}組\n")

# マッチング済みメンバーを抽出
matched_members = set()
for pair in matched_pairs:
    # frozenset から名前を抽出
    for name in pair:
        if name in member_names:
            matched_members.add(name)

# マッチング未実施のメンバーを抽出
unmatched_members = member_names - matched_members

print("[MATCHED] マッチング済みメンバー:")
for name in sorted(matched_members):
    print(f"  [OK] {name}")

print(f"\n[UNMATCHED] マッチング未実施メンバー: {len(unmatched_members)}名")
for name in sorted(unmatched_members):
    print(f"  [NO] {name}")

print("\n" + "="*60)
print(f"[SUMMARY] マッチング済み: {len(matched_members)}名")
print(f"[SUMMARY] マッチング未実施: {len(unmatched_members)}名")
print("="*60 + "\n")

# 詳細：マッチング履歴の内容
print("[DETAIL] マッチング履歴の組み合わせ:\n")
for i, pair in enumerate(matched_pairs, 1):
    pair_list = list(pair)
    print(f"  {i:2d}. {pair_list[0]:12s} × {pair_list[1]}")

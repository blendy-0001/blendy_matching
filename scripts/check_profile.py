"""テスト太郎と山田太郎のプロフィール詳細確認"""
import sys, io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from notion_client import get_all_members

members = get_all_members()

# 対象メンバーを抽出
target_names = ["テスト 太郎", "山田 太郎"]

print("\n" + "="*60)
print("[PROFILE] 詳細プロフィール確認")
print("="*60 + "\n")

for target_name in target_names:
    member = next((m for m in members if m.get('名前') == target_name), None)
    
    if not member:
        print(f"[NOT FOUND] {target_name}\n")
        continue
    
    print(f"【{target_name}】")
    print(f"  会社名: {member.get('会社名', 'N/A')}")
    print(f"  業種カテゴリ: {member.get('業種カテゴリ', 'N/A')}")
    print(f"  業種詳細: {member.get('業種詳細', 'N/A')}")
    print(f"  主力サービス: {member.get('主力サービス', 'N/A')}")
    print(f"  エンドクライアント業界: {member.get('エンドクライアント業界', 'N/A')}")
    print(f"  エンドクライアント規模: {member.get('エンドクライアント規模', 'N/A')}")
    print(f"  クライアントの課題: {member.get('クライアントの課題', 'N/A')}")
    print(f"  バリューチェーン位置: {member.get('バリューチェーン位置', 'N/A')}")
    print(f"  強み: {member.get('強み', 'N/A')}")
    print(f"  課題・足りないもの: {member.get('課題・足りないもの', 'N/A')}")
    print(f"  保有アセット: {member.get('保有アセット', 'N/A')}")
    print(f"  事業フェーズ: {member.get('事業フェーズ', 'N/A')}")
    print()

# 全メンバーのスコアを計算（テスト太郎・山田太郎とのマッチング）
from matching_engine import _score_pair_rules

print("="*60)
print("[SCORING] スコアリング詳細分析")
print("="*60 + "\n")

target_members = [m for m in members if m.get('名前') in target_names]

for target in target_members:
    print(f"【{target.get('名前')}】とのマッチングスコア:\n")
    
    scores = []
    for other in members:
        if target.get('名前') == other.get('名前'):
            continue
        
        result = _score_pair_rules(target, other)
        if result:
            scores.append({
                '相手': other.get('名前'),
                'スコア': result['スコア'],
                'エンドクライアント': result['内訳'].get('エンドクライアント一致度', 0),
                'バリューチェーン': result['内訳'].get('バリューチェーン接続性', 0),
                '市場フィット': result['内訳'].get('市場ソリューションフィット', 0),
                '事業拡張': result['内訳'].get('事業拡張ポテンシャル', 0),
            })
    
    # スコア降順でソート
    scores.sort(key=lambda x: x['スコア'], reverse=True)
    
    # 上位5件を表示
    for i, s in enumerate(scores[:5], 1):
        print(f"  {i}. {s['相手']:12s} → {s['スコア']:2d}点 "
              f"(C{s['エンドクライアント']:2d} "
              f"V{s['バリューチェーン']:2d} "
              f"M{s['市場フィット']:2d} "
              f"E{s['事業拡張']:2d})")
    
    matching_count = sum(1 for s in scores if s['スコア'] >= 50)
    print(f"\n  スコア50以上の候補: {matching_count}件")
    print()

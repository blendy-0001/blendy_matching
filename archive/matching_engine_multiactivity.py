"""
マルチアクティビティ対応 マッチングエンジン
各アクティビティ単位での相互補完性を評価し、複数のマッチパターンを検出
"""

import itertools
from typing import List, Dict, Tuple
from cooperation_type_recommender import infer_cooperation_type, COOPERATION_TYPES


# ===== データ構造 =====

class Activity:
    """事業アクティビティ"""
    def __init__(self, name: str, service: str, strengths: List[str], challenges: List[str],
                 value_chain_positions: List[str], target_industries: List[str], target_size: str):
        self.name = name
        self.service = service
        self.strengths = strengths
        self.challenges = challenges
        self.value_chain_positions = value_chain_positions
        self.target_industries = target_industries
        self.target_size = target_size


class Member:
    """マッチング対象者（複数アクティビティ対応）"""
    def __init__(self, member_id: str, name: str, company: str, phase: str, activities: List[Activity]):
        self.member_id = member_id
        self.name = name
        self.company = company
        self.phase = phase
        self.activities = activities  # 1個以上


# ===== スコアリング関数 =====

def score_activity_pair(activity_a: Activity, activity_b: Activity) -> Dict:
    """
    2つのアクティビティ間の相互補完性をスコアリング

    返り値：
    {
        'total': 0-100,
        'category': 'role_division' | 'market_expansion' | 'resource_share',
        'type': 'A型' | 'B型' | ... | 'G型',
        'reasoning': str,
        'detail': {
            'strength_match': score,
            'challenge_match': score,
            'value_chain_match': score,
            'target_client_match': score
        }
    }
    """

    scores = {'strength': 0, 'challenge': 0, 'value_chain': 0, 'target_client': 0}
    reasoning = []

    # ===== 1. 強み ✕ 課題のマッチング =====
    # A側の強みが、B側の課題を補完できるか
    if set(activity_a.strengths) & set(activity_b.challenges):
        scores['strength'] += 25
        reasoning.append(f"A側の強み {activity_a.strengths} が B側の課題を補完")

    # B側の強みが、A側の課題を補完できるか
    if set(activity_b.strengths) & set(activity_a.challenges):
        scores['strength'] += 25
        reasoning.append(f"B側の強み {activity_b.strengths} が A側の課題を補完")

    # ===== 2. バリューチェーン位置のコンプレメンタリティ =====
    # 営業 → 開発、マーケティング → 営業 など、パイプライン上で相互補完的か
    chain_complements = {
        "認知・ブランディング": ["集客・マーケティング", "営業・提案・クロージング"],
        "集客・マーケティング": ["リード獲得・見込み客育成", "営業・提案・クロージング"],
        "リード獲得・見込み客育成": ["営業・提案・クロージング"],
        "営業・提案・クロージング": ["制作・開発・導入", "運用・保守・継続支援"],
        "制作・開発・導入": ["運用・保守・継続支援"],
        "運用・保守・継続支援": ["営業・提案・クロージング"],  # 既存顧客への追加販売
    }

    chain_match_count = 0
    for pos_a in activity_a.value_chain_positions:
        for pos_b in activity_b.value_chain_positions:
            # A→B方向の補完
            if pos_a in chain_complements and pos_b in chain_complements[pos_a]:
                chain_match_count += 1
            # B→A方向の補完
            if pos_b in chain_complements and pos_a in chain_complements[pos_b]:
                chain_match_count += 1

    if chain_match_count > 0:
        scores['value_chain'] = min(30, chain_match_count * 10)
        reasoning.append(f"バリューチェーン位置が{chain_match_count}パターン相互補完")

    # ===== 3. ターゲットクライアントの一致度 =====
    # 同じターゲット業界・規模を狙っているか（同じ顧客に対して相互補完）
    industry_match = len(set(activity_a.target_industries) & set(activity_b.target_industries))
    size_match = 1 if activity_a.target_size == activity_b.target_size else 0

    if industry_match > 0:
        scores['target_client'] += 15
        reasoning.append(f"対象業界が{industry_match}個合致（共通の顧客に営業可能）")

    if size_match:
        scores['target_client'] += 10
        reasoning.append(f"対象企業規模が一致")

    # ===== 総合スコア =====
    total = sum(scores.values())

    # ===== 協業タイプの推奨 =====
    challenges_a = activity_a.challenges
    challenges_b = activity_b.challenges
    strengths_a = activity_a.strengths
    strengths_b = activity_b.strengths
    value_chain_a = activity_a.value_chain_positions
    value_chain_b = activity_b.value_chain_positions

    # 簡易的な型判定（本来は infer_cooperation_type を使用）
    coop_type = infer_cooperation_type(
        challenges=list(set(challenges_a + challenges_b)),
        strengths=list(set(strengths_a + strengths_b)),
        value_chain_positions=list(set(value_chain_a + value_chain_b)),
        business_phase="成長期",  # 実装時は member の phase を使用
        service_content=f"{activity_a.name}: {activity_a.service} | {activity_b.name}: {activity_b.service}"
    )

    return {
        'total': total,
        'category': categorize_by_equity(activity_a, activity_b),
        'type': coop_type[0],  # 推奨協業型
        'reasoning': " | ".join(reasoning) if reasoning else "標準マッチング",
        'detail': scores
    }


def categorize_by_equity(activity_a: Activity, activity_b: Activity) -> str:
    """
    3つのカテゴリにより分類
    - role_division: A側が営業、B側が開発など役割分担
    - market_expansion: 同じバリューチェーン位置で異なる市場展開
    - resource_share: リソース・キャパシティの相互補完
    """

    # バリューチェーン位置が異なるか
    positions_differ = not bool(set(activity_a.value_chain_positions) & set(activity_b.value_chain_positions))

    # ターゲット業界が同じか
    industries_same = bool(set(activity_a.target_industries) & set(activity_b.target_industries))

    # リソース課題を持つか
    has_resource_challenge = (
        "資金・リソース" in activity_a.challenges or
        "資金・リソース" in activity_b.challenges
    )

    if positions_differ and industries_same:
        return 'role_division'  # 役割分担型
    elif not positions_differ and industries_same:
        return 'market_expansion'  # 市場拡大型
    elif has_resource_challenge:
        return 'resource_share'  # リソース補完型
    else:
        return 'role_division'  # デフォルト


def score_pair_multiactivity(member_a: Member, member_b: Member, min_score: int = 45) -> Dict:
    """
    複数アクティビティを持つメンバー間の全体マッチングスコア

    返り値：
    {
        'overall_score': 0-100,
        'primary_match': (activity_a_name, activity_b_name),
        'match_type': 'A型' | 'B型' | ... | 'G型',
        'all_matches': [
            {
                'activity_a': activity_a.name,
                'activity_b': activity_b.name,
                'score': {...},
                'details': {...}
            },
            ...
        ],
        'justification': str
    }
    """

    all_matches = []
    matched_pairs = []

    # 全アクティビティペアの組み合わせをスコア
    for activity_a in member_a.activities:
        for activity_b in member_b.activities:
            score = score_activity_pair(activity_a, activity_b)

            if score['total'] >= min_score:
                all_matches.append({
                    'activity_a': activity_a.name,
                    'activity_b': activity_b.name,
                    'activity_a_obj': activity_a,
                    'activity_b_obj': activity_b,
                    'score': score
                })
                matched_pairs.append((activity_a.name, activity_b.name, score['total']))

    # マッチがない場合
    if not all_matches:
        return {
            'overall_score': 0,
            'primary_match': None,
            'match_type': None,
            'all_matches': [],
            'justification': f"MIN_SCORE({min_score}) 以上のマッチがありません"
        }

    # ベストマッチを取得（最高スコア）
    best_match = max(all_matches, key=lambda x: x['score']['total'])
    overall_score = best_match['score']['total']

    # 複数のマッチパターンがある場合の説明
    match_count = len(all_matches)
    justification = f"{match_count}個のマッチパターン検出。"
    justification += f"最高スコア: {best_match['activity_a']} × {best_match['activity_b']} = {best_match['score']['total']}"

    return {
        'overall_score': overall_score,
        'primary_match': (best_match['activity_a'], best_match['activity_b']),
        'match_type': best_match['score']['type'],
        'category': best_match['score']['category'],
        'all_matches': all_matches,
        'justification': justification
    }


def run_matching_multiactivity(
    members: List[Member],
    max_matches: int = 15,
    min_score: int = 45,
    existing_pairs: set = None
) -> List[Dict]:
    """
    マルチアクティビティ対応のマッチング実行

    Args:
        members: Member オブジェクトのリスト
        max_matches: 最大マッチ数
        min_score: 最小スコア閾値
        existing_pairs: 既存マッチのセット（frozenset の形式）

    Returns:
        マッチング結果のリスト
    """

    if existing_pairs is None:
        existing_pairs = set()

    # 全メンバーペアのスコア計算
    scored_pairs = []

    for member_a, member_b in itertools.combinations(members, 2):
        # 既存マッチをスキップ
        pair_id = frozenset([member_a.member_id, member_b.member_id])
        if pair_id in existing_pairs:
            continue

        # スコアリング
        score_result = score_pair_multiactivity(member_a, member_b, min_score)

        if score_result['overall_score'] > 0:
            scored_pairs.append({
                'メンバーA': member_a.company,
                'メンバーA_名前': member_a.name,
                'メンバーA_ID': member_a.member_id,
                'メンバーB': member_b.company,
                'メンバーB_名前': member_b.name,
                'メンバーB_ID': member_b.member_id,
                'スコア': score_result['overall_score'],
                '協業タイプ': score_result['match_type'],
                'カテゴリ': score_result['category'],
                'マッチパターン数': len(score_result['all_matches']),
                'プライマリマッチ': score_result['primary_match'],
                '説明': score_result['justification'],
                '詳細マッチ': score_result['all_matches']
            })

    # スコアの高い順にソート
    scored_pairs.sort(key=lambda x: (-x['スコア'], x['メンバーA'], x['メンバーB']))

    # 1人1組制限を適用
    selected_pairs = []
    used_members = set()

    for pair in scored_pairs:
        if pair['メンバーA_ID'] not in used_members and pair['メンバーB_ID'] not in used_members:
            selected_pairs.append(pair)
            used_members.add(pair['メンバーA_ID'])
            used_members.add(pair['メンバーB_ID'])

            if len(selected_pairs) >= max_matches:
                break

    return selected_pairs


# ===== テスト用サンプルデータ =====

if __name__ == "__main__":
    # 人材紹介会社のサンプル
    activities_staffing = [
        Activity(
            name="人材紹介",
            service="採用企業向けエグゼクティブ人材紹介。年間売上3億。",
            strengths=["営業・ネットワーク", "業界知見"],
            challenges=["営業・マーケティング"],
            value_chain_positions=["営業・提案・クロージング"],
            target_industries=["製造業", "金融業"],
            target_size="大企業300名〜"
        ),
        Activity(
            name="交流会主催",
            service="フリーランス向けマッチングイベント。月1回開催。",
            strengths=["営業・ネットワーク"],
            challenges=["認知度拡大"],
            value_chain_positions=["認知・ブランディング", "リード獲得・見込み客育成"],
            target_industries=["IT", "スタートアップ"],
            target_size="個人・フリーランス"
        )
    ]

    member_staffing = Member(
        member_id="m001",
        name="田中太郎",
        company="人材紹介会社A",
        phase="成長期",
        activities=activities_staffing
    )

    # マーケティング会社のサンプル
    activities_marketing = [
        Activity(
            name="Webマーケティング",
            service="BtoB企業向けのWebマーケティング・SEO支援",
            strengths=["技術・開発", "コンテンツ"],
            challenges=["営業・マーケティング"],
            value_chain_positions=["集客・マーケティング", "認知・ブランディング"],
            target_industries=["IT", "SaaS"],
            target_size="スモールビジネス〜10名"
        )
    ]

    member_marketing = Member(
        member_id="m002",
        name="山田花子",
        company="マーケティング会社B",
        phase="成長期",
        activities=activities_marketing
    )

    # マッチング実行
    results = run_matching_multiactivity([member_staffing, member_marketing], max_matches=5)

    print("=== マッチング結果 ===")
    for result in results:
        print(f"\n{result['メンバーA']} ({result['メンバーA_名前']}) × {result['メンバーB']} ({result['メンバーB_名前']})")
        print(f"  スコア: {result['スコア']}")
        print(f"  協業タイプ: {result['協業タイプ']}")
        print(f"  マッチパターン数: {result['マッチパターン数']}")
        print(f"  プライマリマッチ: {result['プライマリマッチ']}")
        print(f"  説明: {result['説明']}")

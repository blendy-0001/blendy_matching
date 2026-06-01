#!/usr/bin/env python3
"""
In-memory matching simulation
Validates matching accuracy using test data without Notion API dependency

Usage: python test_matching_simulation.py
"""

import sys
import re
from typing import Set

# ── Test Members (In-memory) ────────────────────────────
TEST_MEMBERS = [
    {
        "名前": "太郎（SaaS開発社）",
        "会社名": "TechVenture Inc.",
        "業種カテゴリ": "SaaS / IT",
        "事業フェーズ": "成長期",
        "全対象業界": {"医療", "金融", "教育"},
        "全強み": ["Web開発", "API設計", "データベース構設"],
        "全課題": ["営業", "マーケティング", "顧客支援"],
        "全ポジション": ["CTO", "開発"],
        "対象企業規模_list": ["スタートアップ", "中堅企業"],
        "サービス内容_キーワード": "カスタムWeb開発 API統合 クラウドインフラ構築",
    },
    {
        "名前": "花子（営業・マーケティング）",
        "会社名": "GrowthMarketing Co.",
        "業種カテゴリ": "営業支援 / マーケティング",
        "事業フェーズ": "成長期",
        "全対象業界": {"SaaS", "金融", "不動産"},
        "全強み": ["営業", "マーケティング", "リード生成", "顧客開拓"],
        "全課題": ["システム開発", "技術的なサポート"],
        "全ポジション": ["営業", "マーケティング"],
        "対象企業規模_list": ["スタートアップ", "大企業"],
        "サービス内容_キーワード": "営業代行 マーケティング支援 顧客開拓",
    },
    {
        "名前": "次郎（DB最適化・運用）",
        "会社名": "DataOptimize Ltd.",
        "業種カテゴリ": "インフラ / 運用",
        "事業フェーズ": "成熟期",
        "全対象業界": {"金融", "EC", "医療"},
        "全強み": ["データベース", "システム運用", "パフォーマンス最適化", "セキュリティ"],
        "全課題": ["営業戦略", "市場展開"],
        "全ポジション": ["CTO", "運用", "セキュリティ"],
        "対象企業規模_list": ["中堅企業", "大企業"],
        "サービス内容_キーワード": "DB最適化 パフォーマンスチューニング セキュリティ監査",
    },
    {
        "名前": "美咲（ブランディング・デザイン）",
        "会社名": "BrandLab Design.",
        "業種カテゴリ": "ブランディング / デザイン",
        "事業フェーズ": "成長期",
        "全対象業界": {"SaaS", "ファッション", "飲食"},
        "全強み": ["UI/UXデザイン", "ブランディング", "クリエイティブ"],
        "全課題": ["営業", "技術サポート", "マーケティング実装"],
        "全ポジション": ["デザイナー", "企画"],
        "対象企業規模_list": ["スタートアップ", "中堅企業"],
        "サービス内容_キーワード": "UIデザイン ブランディング 企業ロゴ制作",
    },
    {
        "名前": "健太（営業・事業開発）",
        "会社名": "BusinessGrowth Partners.",
        "業種カテゴリ": "営業 / 事業開発",
        "事業フェーズ": "成長期",
        "全対象業界": {"SaaS", "医療", "教育", "金融"},
        "全強み": ["営業", "事業開発", "パートナーシップ", "ネットワーク"],
        "全課題": ["システム開発", "技術知識", "オペレーション"],
        "全ポジション": ["営業", "事業開発"],
        "対象企業規模_list": ["スタートアップ", "中堅企業", "大企業"],
        "サービス内容_キーワード": "営業支援 ビジネス開発 パートナーマッチング",
    },
    {
        "名前": "研究員（AI・データサイエンス）",
        "会社名": "AI Research Labs.",
        "業種カテゴリ": "AI / データサイエンス",
        "事業フェーズ": "成長期",
        "全対象業界": {"医療", "金融", "製造"},
        "全強み": ["機械学習", "データ分析", "AI モデル開発"],
        "全課題": ["営業", "マーケティング", "プロダクト化"],
        "全ポジション": ["データサイエンティスト", "開発"],
        "対象企業規模_list": ["大企業"],
        "サービス内容_キーワード": "機械学習モデル開発 データ分析 AI導入支援",
    },
]


def _text_overlap(text1: str, text2: str, min_overlap: int = 1) -> bool:
    """2つのテキストに共通の単語が含まれているか判定"""
    if not text1 or not text2:
        return False

    words1 = set(re.split(r'[\s、，、。・]+', text1.lower().strip()))
    words2 = set(re.split(r'[\s、，、。・]+', text2.lower().strip()))

    words1.discard('')
    words2.discard('')

    words1 = {w for w in words1 if len(w) >= 2}
    words2 = {w for w in words2 if len(w) >= 2}

    overlap_count = len(words1 & words2)
    return overlap_count >= min_overlap


def _calc_client_fit(a: dict, b: dict) -> int:
    """エンドクライアント一致度（0-20点）"""
    score = 0

    # 対象業界の重複
    a_industries = a.get("全対象業界", set())
    b_industries = b.get("全対象業界", set())
    if a_industries & b_industries:
        score += 4

    # 業種カテゴリの一致
    if a.get("業種カテゴリ") and a.get("業種カテゴリ") == b.get("業種カテゴリ"):
        score += 3

    # 対象企業規模の相性
    a_sizes = set(a.get("対象企業規模_list", []))
    b_sizes = set(b.get("対象企業規模_list", []))
    if a_sizes & b_sizes:
        score += 2

    # Win-Win 双方向補完性判定
    a_strengths_text = " ".join(a.get("全強み", []))
    a_issues_text = " ".join(a.get("全課題", []))
    b_strengths_text = " ".join(b.get("全強み", []))
    b_issues_text = " ".join(b.get("全課題", []))

    a_helps_b = b_issues_text and a_strengths_text and _text_overlap(a_strengths_text, b_issues_text)
    b_helps_a = a_issues_text and b_strengths_text and _text_overlap(b_strengths_text, a_issues_text)

    if a_helps_b and b_helps_a:
        score += 8
    elif a_helps_b or b_helps_a:
        score += 3

    return min(score, 20)


def _calc_chain_fit(a: dict, b: dict) -> int:
    """バリューチェーン接続性（0-20点）"""
    score = 0

    a_positions = set(a.get("全ポジション", []))
    b_positions = set(b.get("全ポジション", []))

    if not a_positions or not b_positions:
        return 0

    complementary_pairs = [
        ("営業", "製造"),
        ("営業", "企画"),
        ("営業", "開発"),
        ("企画", "開発"),
        ("マーケティング", "営業"),
        ("マーケティング", "開発"),
        ("経営", "営業"),
        ("経営", "開発"),
        ("営業支援", "営業"),
        ("営業支援", "開発"),
        ("CTO", "営業"),
        ("営業開発", "開発"),
    ]

    has_complementary = False
    for pos1, pos2 in complementary_pairs:
        if (pos1 in a_positions and pos2 in b_positions) or (pos2 in a_positions and pos1 in b_positions):
            has_complementary = True
            break

    if has_complementary:
        score += 15

    if a_positions != b_positions and (a_positions | b_positions):
        score += 5

    return min(score, 20)


def _calc_market_fit(a: dict, b: dict) -> int:
    """市場ソリューションフィット（0-20点）"""
    score = 0

    a_strengths = set(a.get("全強み", []))
    b_strengths = set(b.get("全強み", []))
    a_issues = set(a.get("全課題", []))
    b_issues = set(b.get("全課題", []))

    solution_keywords = ["開発", "技術", "システム", "API", "データベース", "デザイン", "製造"]
    market_keywords = ["営業", "マーケティング", "営業支援", "ネットワーク", "顧客", "事業開発"]

    a_has_solution = any(kw in strength for strength in a_strengths for kw in solution_keywords)
    b_has_solution = any(kw in strength for strength in b_strengths for kw in solution_keywords)
    a_has_market = any(kw in strength for strength in a_strengths for kw in market_keywords)
    b_has_market = any(kw in strength for strength in b_strengths for kw in market_keywords)

    a_needs_solution = any(kw in issue for issue in a_issues for kw in solution_keywords)
    b_needs_solution = any(kw in issue for issue in b_issues for kw in solution_keywords)
    a_needs_market = any(kw in issue for issue in a_issues for kw in market_keywords)
    b_needs_market = any(kw in issue for issue in b_issues for kw in market_keywords)

    if (a_has_solution and b_needs_solution and b_has_market and a_needs_market) or \
       (b_has_solution and a_needs_solution and a_has_market and b_needs_market):
        score = 20
    elif (a_has_solution and b_has_market) or (b_has_solution and a_has_market):
        score = 15
    elif a_has_solution or b_has_solution or a_has_market or b_has_market:
        score = 8

    return min(score, 20)


def _calc_expansion_potential(a: dict, b: dict) -> int:
    """事業拡張ポテンシャル（0-20点）"""
    score = 0

    a_strengths = set(a.get("全強み", []))
    b_strengths = set(b.get("全強み", []))
    a_issues = set(a.get("全課題", []))
    b_issues = set(b.get("全課題", []))

    # A の強みが B の課題に対応できるか（逆も同様）
    a_addresses_b = any(kw in strength for strength in a_strengths for kw in b_issues)
    b_addresses_a = any(kw in strength for strength in b_strengths for kw in a_issues)

    if a_addresses_b or b_addresses_a:
        score += 12

    # 事業フェーズの相性（成長期 + 成長期 / 成熟期）
    a_phase = a.get("事業フェーズ", "")
    b_phase = b.get("事業フェーズ", "")

    if a_phase in ["成長期", "拡張期"] and b_phase in ["成長期", "拡張期"]:
        score += 5
    elif a_phase == "成熟期" and b_phase in ["成長期", "拡張期"]:
        score += 3

    return min(score, 20)


def _calc_target_market_fit(a: dict, b: dict) -> int:
    """対象市場一致度（0-20点）"""
    score = 0

    a_service = a.get("サービス内容_キーワード", "")
    b_service = b.get("サービス内容_キーワード", "")

    if _text_overlap(a_service, b_service):
        score += 10

    # 対象業界の重複度を詳細判定
    a_industries = a.get("全対象業界", set())
    b_industries = b.get("全対象業界", set())

    if len(a_industries & b_industries) >= 2:
        score += 10

    return min(score, 20)


def score_pair(a: dict, b: dict) -> dict:
    """ペアをスコアリング"""
    scores = {
        "エンドクライアント一致度": _calc_client_fit(a, b),
        "バリューチェーン接続性": _calc_chain_fit(a, b),
        "市場ソリューションフィット": _calc_market_fit(a, b),
        "事業拡張ポテンシャル": _calc_expansion_potential(a, b),
        "対象市場一致度": _calc_target_market_fit(a, b),
    }

    total_score = min(sum(scores.values()), 100)

    return {
        "メンバーA名": a["名前"],
        "メンバーB名": b["名前"],
        "スコア": total_score,
        "内訳": scores,
    }


def run_simulation():
    """メモリ内シミュレーション実行"""
    print("\n" + "="*70)
    print("[MATCHING ACCURACY SIMULATION]")
    print("="*70)
    print(f"\nTest Members: {len(TEST_MEMBERS)}")
    for i, member in enumerate(TEST_MEMBERS, 1):
        print(f"  {i}. {member['名前']} ({member['会社名']})")

    # Generate pairs
    pairs = []
    for i, a in enumerate(TEST_MEMBERS):
        for b in TEST_MEMBERS[i+1:]:
            pairs.append((a, b))

    print(f"\nTotal Pairs Generated: {len(pairs)}\n")

    # スコアリング
    results = []
    for a, b in pairs:
        result = score_pair(a, b)
        results.append(result)

    # スコアで降順ソート
    results.sort(key=lambda x: -x["スコア"])

    # 分布分析
    min_score = 45
    high_quality = [r for r in results if r["スコア"] >= 75]
    medium_quality = [r for r in results if 60 <= r["スコア"] < 75]
    low_quality = [r for r in results if min_score <= r["スコア"] < 60]
    below_min = [r for r in results if r["スコア"] < min_score]

    print("\n[SCORE DISTRIBUTION]")
    print(f"  High Quality (75+)      : {len(high_quality)} pairs ({100*len(high_quality)//len(results)}%)")
    print(f"  Medium Quality (60-74)  : {len(medium_quality)} pairs ({100*len(medium_quality)//len(results)}%)")
    print(f"  Low Quality (45-59)     : {len(low_quality)} pairs ({100*len(low_quality)//len(results)}%)")
    print(f"  Below Min (<45)         : {len(below_min)} pairs ({100*len(below_min)//len(results)}%)")

    acceptance_rate = (len(high_quality) + len(medium_quality) + len(low_quality)) / len(results) * 100
    print(f"\n  [OK] Matching acceptance rate (>= 45pts): {acceptance_rate:.1f}%")

    # Display detailed results (top 15 pairs)
    print("\n[TOP MATCHING RESULTS (by score)]")
    print("-" * 70)

    for i, result in enumerate(results[:15], 1):
        print(f"\n{i}. {result['メンバーA名']} x {result['メンバーB名']}")
        print(f"   Score: {result['スコア']} pts")
        print(f"   Breakdown: ", end="")
        items = [f"{k}={v}pts" for k, v in result["内訳"].items()]
        print(", ".join(items))

        # Win-Win assessment
        a = next(m for m in TEST_MEMBERS if m["名前"] == result["メンバーA名"])
        b = next(m for m in TEST_MEMBERS if m["名前"] == result["メンバーB名"])

        a_strengths_text = " ".join(a.get("全強み", []))
        a_issues_text = " ".join(a.get("全課題", []))
        b_strengths_text = " ".join(b.get("全強み", []))
        b_issues_text = " ".join(b.get("全課題", []))

        a_helps_b = b_issues_text and a_strengths_text and _text_overlap(a_strengths_text, b_issues_text)
        b_helps_a = a_issues_text and b_strengths_text and _text_overlap(b_strengths_text, a_issues_text)

        if a_helps_b and b_helps_a:
            print(f"   Win-Win: [OK] Mutual complementarity")
        elif a_helps_b or b_helps_a:
            print(f"   Win-Win: [--] Unidirectional complementarity")
        else:
            print(f"   Win-Win: [NO] No complementarity")

    print("\n" + "="*70)
    print("[QUALITY SUMMARY]")
    print("="*70)
    print(f"[A] High Quality (75+)  : {len(high_quality):2d} pairs - Ready for intro")
    print(f"[B] Medium Quality (60-74): {len(medium_quality):2d} pairs - Review then intro")
    print(f"[C] Low Quality (45-59) : {len(low_quality):2d} pairs - Latent synergy target")
    print(f"[X] Below Min (<45)     : {len(below_min):2d} pairs - Filtered out")
    print(f"\nTarget: High > 40%, Medium > 30%")
    print(f"Result: High {100*len(high_quality)//len(results)}%, Medium {100*len(medium_quality)//len(results)}%")

    if len(high_quality) > len(results) * 0.4:
        print("\n[VERDICT] Matching accuracy is EXCELLENT")
    elif len(high_quality) + len(medium_quality) > len(results) * 0.7:
        print("\n[VERDICT] Matching accuracy is GOOD")
    else:
        print("\n[VERDICT] Matching accuracy needs improvement")


if __name__ == "__main__":
    run_simulation()

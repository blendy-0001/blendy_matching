"""
マッチングエンジン
ルールベーススコアリング + Claude API による紹介文生成
"""
import json
import itertools
import os
import logging
from datetime import datetime
import anthropic
from .config import CLAUDE_API_KEY, MIN_SCORE, MAX_MATCHES_PER_RUN, COLLABORATION_TYPES, INDUSTRY_KEYWORDS
from .notion_client import get_activities_for_member, clear_activities_cache

# ロギング設定
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# ── バリューチェーン順序 ──────────────────────
# フォーム（register.html）の選択肢に合わせたバリューチェーン段階
VALUE_CHAIN_ORDER = [
    "認知・ブランディング",
    "集客・マーケティング",
    "リード獲得・見込み客育成",
    "営業・提案・クロージング",
    "制作・開発・導入",
    "運用・保守・継続支援",
    "教育・研修・人材育成",
    "経営・戦略・資金調達",
]

# ── キーワード同義語グループ ──────────────────────
# テキスト判定時に「営業」「セールス」など同じグループの言葉を統一処理
KEYWORD_SYNONYMS = {
    "営業": ["営業", "セールス", "営業開発", "BDR", "営業支援", "営業コンサル"],
    "開発": ["開発", "エンジニアリング", "テック", "技術", "システム構築", "バックエンド", "フロントエンド"],
    "マーケティング": ["マーケティング", "マーケ", "プロモーション", "ブランディング", "広告"],
    "企画": ["企画", "PM", "プロダクト", "ストラテジー", "戦略"],
    "顧客支援": ["顧客成功", "CS", "カスタマーサクセス", "サポート", "カスタマーサポート"],
    "製造": ["製造", "生産", "オペレーション", "実装"],
    "デザイン": ["デザイン", "UI/UX", "ビジュアル", "クリエイティブ"],
    "経営": ["経営", "CEO", "COO", "CFO", "取締役"],
    "コンサル": ["コンサル", "コンサルティング", "アドバイザリー"],
}


def _merge_member_with_activities(member: dict, activities: list[dict]) -> dict:
    """
    メンバー基本情報 + すべての activities をマージして unified profile を構築

    Args:
        member: メンバー基本情報 {"名前": "...", "会社名": "...", ...}
        activities: Activities リスト [{"アクティビティ名": "...", "強み": [...], ...}, ...]

    Returns:
        統合プロフィール dict
    """
    # 基本情報をコピー
    merged = member.copy()

    # 対象業界の統合（set で重複排除）
    industries = set()
    for act in activities:
        industry_text = act.get("対象業界", "").strip()
        if industry_text:
            # カンマ区切りを split（例：「医療、金融」→ {「医療」, 「金融」}）
            for ind in industry_text.split("、"):
                industries.add(ind.strip())
    merged["全対象業界"] = industries

    # 強み・課題・ポジションの統合（重複排除）
    strengths = []
    issues = []
    positions = []

    for act in activities:
        strengths.extend(act.get("強み", []))
        issues.extend(act.get("課題", []))
        positions.extend(act.get("ポジション", []))

    merged["全強み"] = list(set(strengths))  # 重複排除して list に
    merged["全課題"] = list(set(issues))
    merged["全ポジション"] = list(set(positions))

    # 対象企業規模の統合
    sizes = set()
    for act in activities:
        size = act.get("対象企業規模", "").strip()
        if size:
            sizes.add(size)
    merged["対象企業規模_list"] = sorted(list(sizes))

    # キーワード検索用に サービス内容をテキスト化
    service_texts = []
    for act in activities:
        service = act.get("サービス内容", "").strip()
        if service:
            service_texts.append(service)
    merged["サービス内容_キーワード"] = " ".join(service_texts)

    # 活動数（マッチング理由生成用）
    merged["活動数"] = len(activities)

    return merged


def run_matching(members: list[dict], matched_pairs: set[frozenset], max_matches: int = 30) -> tuple[list[dict], list[dict]]:
    """
    メインのマッチング処理
    1. 全ペアを生成（再マッチング除外、ペア単位のみ）
    2. AIでバッチスコアリング
    3. 上位ペアを選定して紹介文を生成

    Args:
        max_matches: 今回のマッチング目標組数（無視され、利用可能メンバー数から自動計算）

    Returns:
        tuple: (マッチング結果のリスト, マッチングされなかった人のリスト)
    """
    # ── Step0: マッチング済みメンバーを抽出 ──────────────────
    matched_members = set()
    for pair in matched_pairs:
        matched_members.update(pair)  # pair は frozenset([名前A, 名前B])

    logger.info(f"過去のマッチング済みメンバー: {len(matched_members)}名")

    # ★自動計算: 利用可能なメンバー数から目標マッチング組数を動的決定
    # （ユーザーの max_matches パラメータは参考値のみ）
    # 利用可能 = 全メンバー数 - 前回マッチング済みメンバー数
    # ただし、前回マッチング済みメンバーも「異なるペア」なら含める
    available_members = len(members)
    auto_max_matches = available_members // 2  # 全メンバーを最大限マッチング
    logger.info(f"全メンバー数: {available_members}名")
    logger.info(f"目標マッチング組数（自動計算）: {auto_max_matches}組")

    # ── Step1: 有効なペアを生成 ──────────────────
    valid_pairs = []
    for a, b in itertools.combinations(members, 2):
        a_name = a["名前"]
        b_name = b["名前"]
        pair_key = frozenset([a_name, b_name])

        # ペアが既にマッチング済みなら除外（同じペアの再マッチング防止）
        if pair_key in matched_pairs:
            continue

        # ★削除: メンバー単位での除外を廃止
        # → 同じ人が複数の異なる相手とマッチング可能に（複数回実行での相互マッチング対応）

        valid_pairs.append((a, b))

    if not valid_pairs:
        # マッチング可能なペアがない場合、全員がマッチングされなかった
        return [], members

    # ── Step1.5: 各メンバーの Activities データを取得して enrichment ──
    logger.info(f"  → {len(members)}名のアクティビティデータを取得中...")
    enriched_members = {}
    for member in members:
        member_name = member["名前"]
        member_id = member["id"]
        try:
            activities = get_activities_for_member(member_id)
            enriched = _merge_member_with_activities(member, activities)
            enriched_members[member_name] = enriched
        except Exception as e:
            logger.error(f"Activity enrichment エラー ({member_name}): {e}")
            # 失敗時は基本情報のみで続行
            enriched_members[member_name] = member

    # ── Step2: ルールベーススコアリング ───────────────────
    logger.info(f"  → {len(valid_pairs)}組をスコアリング中...")
    scored = []
    for a, b in valid_pairs:
        # enriched データでスコアリング
        a_enriched = enriched_members.get(a["名前"], a)
        b_enriched = enriched_members.get(b["名前"], b)
        result = _score_pair_rules(a_enriched, b_enriched)

        # ★潜在シナジー検知（スコア 45-60 点帯のみ）
        if result and 45 <= result["スコア"] <= 60:
            final_score, synergy_reason = _detect_latent_synergy(a_enriched, b_enriched, result["スコア"])
            if final_score != result["スコア"]:
                logger.info(f"  → 潜在シナジー検知: {result['メンバーA名']} × {result['メンバーB名']} ({result['スコア']} → {final_score}点) [{synergy_reason}]")
                result["スコア"] = final_score
                result["潜在シナジー"] = synergy_reason

        if result and result["スコア"] >= MIN_SCORE:
            scored.append(result)

    # ── Step3: 上位ペアを選定（1人が複数回選ばれすぎないよう調整）──
    # スコアが同じ場合は、メンバーA名の辞書順でソート（再現性確保）
    scored.sort(key=lambda x: (-x["スコア"], x["メンバーA名"], x["メンバーB名"]))
    selected = _select_balanced_pairs(scored, auto_max_matches)

    # ── Step4: 紹介文を生成 ──────────────────────
    logger.info(f"  → {len(selected)}組の紹介文を生成中...")
    for match in selected:
        match["紹介文"] = _generate_intro(match)

    # ── Step5: マッチングされなかった人を抽出 ──────────────────────
    matched_member_names = set()
    for match in selected:
        matched_member_names.add(match["メンバーA名"])
        matched_member_names.add(match["メンバーB名"])

    unmatched_members = [m for m in members if m["名前"] not in matched_member_names]
    logger.info(f"  → マッチングされなかった人: {len(unmatched_members)}名")

    return selected, unmatched_members


def _score_pair_rules(a: dict, b: dict) -> dict | None:
    """ルールベースでペアをスコアリング（API不使用・高速）"""
    try:
        # ── スコアリング計算 ──
        scores = {
            "エンドクライアント一致度": _calc_client_fit(a, b),
            "バリューチェーン接続性": _calc_chain_fit(a, b),
            "市場ソリューションフィット": _calc_market_fit(a, b),
            "事業拡張ポテンシャル": _calc_expansion_potential(a, b),
            "対象市場一致度": _calc_target_market_fit(a, b),  # Phase 1追加
        }

        total_score = min(sum(scores.values()), 100)  # スコアを100以下にキャップ
        collab_type = _determine_collab_type(a, b, scores)
        reason = _generate_reason(a, b, scores)

        return {
            "メンバーA名": a["名前"],
            "メンバーB名": b["名前"],
            "メンバーA": a,
            "メンバーB": b,
            "スコア": total_score,
            "内訳": scores,
            "協業タイプ": collab_type,
            "マッチング理由": reason,
        }
    except Exception as e:
        logger.error(f"    スコアリングエラー ({a['名前']} × {b['名前']}): {e}")
        return None


def _normalize_word_with_synonyms(word: str) -> str:
    """1つのワードを同義語グループの代表語に正規化

    例: "セールス" → "営業", "エンジニアリング" → "開発"
    """
    word_lower = word.lower().strip()
    for group_key, synonyms in KEYWORD_SYNONYMS.items():
        if word_lower in [s.lower() for s in synonyms]:
            return group_key
    return word_lower


def _normalize_with_synonyms(words: set) -> set:
    """単語セットを同義語正規化

    Args:
        words: 元の単語セット（例：{"営業", "セールス", "web開発"}）

    Returns:
        正規化済みセット（例：{"営業", "開発"}）
    """
    return {_normalize_word_with_synonyms(w) for w in words}


def _text_overlap_with_synonyms(text1: str, text2: str) -> bool:
    """同義語対応テキスト重複検出

    テキストから単語を抽出し、同義語グループレベルで重複を判定
    これにより「Web開発」と「Webマーケティング」の「Web」での誤マッチを防止

    例:
      - text1 = "営業開発とセールスコンサル"
      - text2 = "営業支援とマーケティング"
      → 両方に「営業」グループが含まれるので True

    Args:
        text1: 比較対象テキスト1
        text2: 比較対象テキスト2

    Returns:
        同義語グループレベルで1つ以上の重複がある場合 True
    """
    if not text1 or not text2:
        return False

    # 簡易分割：スペース、カンマ、句読点で分割
    import re
    words1 = set(re.split(r'[\s、，、。・]+', text1.lower().strip()))
    words2 = set(re.split(r'[\s、，、。・]+', text2.lower().strip()))

    # 空文字列を除外
    words1.discard('')
    words2.discard('')

    # 2文字以上のワードのみ判定
    words1 = {w for w in words1 if len(w) >= 2}
    words2 = {w for w in words2 if len(w) >= 2}

    # ★同義語グループレベルで正規化
    normalized1 = _normalize_with_synonyms(words1)
    normalized2 = _normalize_with_synonyms(words2)

    # グループレベルで重複があるかチェック
    return bool(normalized1 & normalized2)


def _has_strength_keyword(member: dict, keywords: list[str]) -> bool:
    """
    強みのキーワードを判定

    注: 強みの詳細情報は Activities DB にあるため、メンバー基本情報からは判定不可
    マルチアクティビティ対応時に Activities DB から統合予定
    """
    return False


def _has_gap_keyword(member: dict, keywords: list[str]) -> bool:
    """
    課題のキーワードを判定

    注: 課題の詳細情報は Activities DB にあるため、メンバー基本情報からは判定不可
    マルチアクティビティ対応時に Activities DB から統合予定
    """
    return False


def _calc_client_fit(a: dict, b: dict) -> int:
    """エンドクライアント一致度（0-20点）

    ★Win-Win判定: 双方向の補完性を確認
    """
    score = 0

    # 対象業界の重複
    a_industries = a.get("全対象業界", set())
    b_industries = b.get("全対象業界", set())
    if a_industries & b_industries:
        score += 4

    # 業種カテゴリの一致（同じクライアント層か）
    if a.get("業種カテゴリ") and a.get("業種カテゴリ") == b.get("業種カテゴリ"):
        score += 3

    # 対象企業規模の相性
    a_sizes = set(a.get("対象企業規模_list", []))
    b_sizes = set(b.get("対象企業規模_list", []))
    if a_sizes & b_sizes:
        score += 2

    # ★★★ Win-Win 双方向補完性判定 ★★★
    a_strengths_text = " ".join(a.get("全強み", []))
    a_issues_text = " ".join(a.get("全課題", []))
    b_strengths_text = " ".join(b.get("全強み", []))
    b_issues_text = " ".join(b.get("全課題", []))

    # A の強みが B の課題を解決できるか（同義語対応）
    a_helps_b = b_issues_text and a_strengths_text and _text_overlap_with_synonyms(a_strengths_text, b_issues_text)
    # B の強みが A の課題を解決できるか（同義語対応）
    b_helps_a = a_issues_text and b_strengths_text and _text_overlap_with_synonyms(b_strengths_text, a_issues_text)

    if a_helps_b and b_helps_a:
        # ★完全な Win-Win（双方が双方の課題を解決できる）
        score += 8
    elif a_helps_b or b_helps_a:
        # 片方向のみ（一方が相手を助けられる）
        score += 3

    return min(score, 20)


def _calc_chain_fit(a: dict, b: dict) -> int:
    """バリューチェーン接続性（0-20点）

    ポジション (multi_select) の相補性：営業×製造、企画×開発など
    """
    score = 0

    a_positions = set(a.get("全ポジション", []))
    b_positions = set(b.get("全ポジション", []))

    if not a_positions or not b_positions:
        return 0

    # 相補的なポジション組み合わせを判定
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
    ]

    # 相補的なペアが存在するか
    has_complementary = False
    for pos1, pos2 in complementary_pairs:
        if (pos1 in a_positions and pos2 in b_positions) or (pos2 in a_positions and pos1 in b_positions):
            has_complementary = True
            break

    if has_complementary:
        score += 15

    # 完全に異なるポジションセットがあるか（バリューチェーン的多様性）
    if a_positions != b_positions and (a_positions | b_positions):
        score += 5

    return min(score, 20)


def _calc_market_fit(a: dict, b: dict) -> int:
    """市場ソリューションフィット（0-20点）- 拡張版

    50+個の業界キーワードで「技術×営業」などの補完性を判定（Priority 2）
    """
    score = 0

    a_strengths = set(a.get("全強み", []))
    b_strengths = set(b.get("全強み", []))
    a_issues = set(a.get("全課題", []))
    b_issues = set(b.get("全課題", []))

    # ★拡張版：3カテゴリ × 50+ キーワードで判定
    solution_keywords = INDUSTRY_KEYWORDS.get("ソリューション系", [])
    market_keywords = INDUSTRY_KEYWORDS.get("マーケット系", [])
    industry_keywords = INDUSTRY_KEYWORDS.get("業界別", [])

    # 各カテゴリでの保有状況をチェック
    a_has_solution = any(kw in strength for strength in a_strengths for kw in solution_keywords)
    b_has_solution = any(kw in strength for strength in b_strengths for kw in solution_keywords)
    a_has_market = any(kw in strength for strength in a_strengths for kw in market_keywords)
    b_has_market = any(kw in strength for strength in b_strengths for kw in market_keywords)
    a_has_industry = any(kw in strength for strength in a_strengths for kw in industry_keywords)
    b_has_industry = any(kw in strength for strength in b_strengths for kw in industry_keywords)

    # 課題側でのニーズをチェック
    a_needs_solution = any(kw in issue for issue in a_issues for kw in solution_keywords)
    b_needs_solution = any(kw in issue for issue in b_issues for kw in solution_keywords)
    a_needs_market = any(kw in issue for issue in a_issues for kw in market_keywords)
    b_needs_market = any(kw in issue for issue in b_issues for kw in market_keywords)

    # ★パターン1: 完全補完（一方が強みで他方が課題）
    if (a_has_solution and b_needs_solution and b_has_market and a_needs_market) or \
       (b_has_solution and a_needs_solution and a_has_market and b_needs_market):
        score = 20

    # ★パターン2: ソリューション × 市場の直接補完
    elif (a_has_solution and b_has_market) or (b_has_solution and a_has_market):
        score = 15

    # ★パターン3: 業界別での相乗効果（新規）
    elif a_has_industry and b_has_industry:
        # 同じ業界キーワードを持つ場合、協業による市場拡大の可能性
        a_industries = {s for s in a_strengths if any(kw in s for kw in industry_keywords)}
        b_industries = {s for s in b_strengths if any(kw in s for kw in industry_keywords)}
        if a_industries & b_industries:  # 同じ業界キーワードがある
            score = 12

    # ★パターン4: 部分的な補完
    elif ((a_has_solution or a_has_market or a_has_industry) and
          (b_has_solution or b_has_market or b_has_industry)):
        score = 8

    return min(score, 20)


def _calc_expansion_potential(a: dict, b: dict) -> int:
    """事業拡張ポテンシャル（20点満点）"""
    score = 0

    # 業種の異なり（新市場の可能性）
    if a.get("業種カテゴリ") != b.get("業種カテゴリ"):
        score += 12

    # 事業フェーズの相性
    phase_a = a.get("事業フェーズ", "")
    phase_b = b.get("事業フェーズ", "")

    if (phase_a == "成長期" and phase_b == "成長期"):
        score += 5  # 両方成長期 = 相乗効果
    elif (phase_a == "安定期" and phase_b == "成長期") or \
         (phase_a == "成長期" and phase_b == "安定期"):
        score += 4  # 安定期が成長期をサポート
    else:
        score += 2  # その他の組み合わせもポイント

    return min(score, 20)


def _calc_target_market_fit(a: dict, b: dict) -> int:
    """対象市場一致度（0-20点）

    対象業界の重複を判定してスコアリング
    """
    score = 0

    a_industries = a.get("全対象業界", set())
    b_industries = b.get("全対象業界", set())

    if not a_industries or not b_industries:
        return 0

    # 対象業界の重複数
    overlap = a_industries & b_industries
    if overlap:
        # 重複数が多いほど高スコア
        overlap_count = len(overlap)
        score = min(overlap_count * 5, 20)  # max 20点

    return score


def _detect_latent_synergy(a: dict, b: dict, rule_score: int) -> tuple[int, str]:
    """潜在シナジー検知（属性マトリクス判定 + LLM スポット投入）

    スコア 45-60 点帯のペアのみに適用して、隠れたシナジーを検知
    返却: (最終スコア, 潜在シナジー説明)
    """
    if rule_score < 45 or rule_score > 60:
        return rule_score, ""  # スコア帯外は LLM 不使用

    # ★属性マトリクス判定（LLM 前の Heuristics）
    synergy_signals = []

    # Signal 1: 事業フェーズの相乗効果（成長期 + 安定期）
    a_phase = a.get("事業フェーズ", "")
    b_phase = b.get("事業フェーズ", "")
    if (a_phase == "成長期" and b_phase == "安定期") or \
       (a_phase == "安定期" and b_phase == "成長期"):
        synergy_signals.append("フェーズ相乗")

    # Signal 2: バリューチェーン上の補完性（上流 × 下流）
    a_positions = set(a.get("全ポジション", []))
    b_positions = set(b.get("全ポジション", []))
    upstream = {"認知・ブランディング", "集客・マーケティング", "リード獲得・見込み客育成"}
    downstream = {"営業・提案・クロージング", "制作・開発・導入", "運用・保守・継続支援"}

    a_is_upstream = bool(a_positions & upstream)
    a_is_downstream = bool(a_positions & downstream)
    b_is_upstream = bool(b_positions & upstream)
    b_is_downstream = bool(b_positions & downstream)

    if (a_is_upstream and b_is_downstream) or (a_is_downstream and b_is_upstream):
        synergy_signals.append("バリューチェーン補完")

    # Signal 3: 顧客層の相補性（SMB × 大企業）
    a_sizes = set(a.get("対象企業規模_list", []))
    b_sizes = set(b.get("対象企業規模_list", []))
    smb = {"個人・フリーランス", "スモールビジネス〜10名", "中小企業10〜300名"}
    large = {"大企業300名〜"}

    a_is_smb = bool(a_sizes & smb)
    a_is_large = bool(a_sizes & large)
    b_is_smb = bool(b_sizes & smb)
    b_is_large = bool(b_sizes & large)

    if (a_is_smb and b_is_large) or (a_is_large and b_is_smb):
        synergy_signals.append("企業規模補完")

    # シナジーシグナルが 2 個以上ある場合のみ LLM 投入
    if len(synergy_signals) >= 2:
        llm_boost = _analyze_latent_synergy_with_llm(a, b, synergy_signals)
        final_score = min(rule_score + llm_boost, 100)
        return final_score, " + ".join(synergy_signals)

    return rule_score, ""


def _analyze_latent_synergy_with_llm(a: dict, b: dict, signals: list[str]) -> int:
    """LLM で潜在シナジーを分析（スコア 45-60 点帯のみ）

    返却: +0〜10 点（規則ベーススコアに加算）
    """
    prompt = f"""
## 企業 A: {a.get('名前', '')}
- 業種: {a.get('業種カテゴリ', '')}
- サービス: {a.get('サービス内容_キーワード', '')[:150]}
- 強み: {', '.join(a.get('全強み', [])[:3])}
- 課題: {', '.join(a.get('全課題', [])[:3])}

## 企業 B: {b.get('名前', '')}
- 業種: {b.get('業種カテゴリ', '')}
- サービス: {b.get('サービス内容_キーワード', '')[:150]}
- 強み: {', '.join(b.get('全強み', [])[:3])}
- 課題: {', '.join(b.get('全課題', [])[:3])}

## 検出されたシナジーシグナル
{', '.join(signals)}

以下を分析し、潜在的なシナジーが存在するか判定してください：
1. 異業種での知見・ノウハウ移転の可能性
2. 顧客層の重複による市場拡大
3. 補完的なリソース・スキルセット
4. 隠れた相互利益の機会

**JSON形式で応答してください:**
{"有潜在シナジー": true/false, "加算点": 0-10, "理由": "一行説明"}
"""

    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=80,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        result = json.loads(msg.content[0].text)
        return result.get("加算点", 0) if result.get("有潜在シナジー") else 0

    except Exception as e:
        logger.debug(f"LLM synergy analysis failed: {e}")
        return 0  # LLM 失敗時は加算なし


def _parse_industries(industry_str: str) -> list[str]:
    """
    対象業界文字列をパース（複数業界対応）

    入力例：
    - 「医療」（単一）
    - 「医療、バイオ」（日本語カンマ区切り）
    - 「医療,バイオ」（ASCII カンマ区切り）
    - 「医療/バイオ」（スラッシュ区切り）
    - 「医療 バイオ」（スペース区切り）

    戻り値：['医療', 'バイオ']
    """
    if not industry_str:
        return []

    # 日本語カンマ、ASCII カンマ、スラッシュ、スペースで分割
    import re
    # 日本語の「、」と「、」の両方に対応
    industries = re.split(r'[,、/\s]+', industry_str.strip())

    # 空文字列を除去、重複を除去
    industries = [ind.strip() for ind in industries if ind.strip()]
    return list(dict.fromkeys(industries))  # 順序を保持しながら重複除去


def _determine_collab_type(a: dict, b: dict, scores: dict) -> str:
    """スコア内訳から最適な協業タイプを判定"""
    chain = scores["バリューチェーン接続性"]
    market = scores["市場ソリューションフィット"]
    client = scores["エンドクライアント一致度"]
    target_market = scores["対象市場一致度"]

    if chain == 25:
        return "A バリューチェーン型"
    elif market >= 15:
        return "B 市場参入型"
    elif client >= 15:
        return "C バンドル強化型"
    elif target_market >= 10:
        return "C バンドル強化型"  # 対象市場一致が高い場合も同じ市場狙いで相乗効果あり
    elif _has_strength_keyword(a, ["技術・開発"]) and \
         _has_strength_keyword(b, ["営業・ネットワーク"]):
        return "D OEM・裏方型"
    elif scores["事業拡張ポテンシャル"] >= 10:
        return "F 共同開発型"
    else:
        return "E 相互紹介型"


def _generate_reason(a: dict, b: dict, scores: dict) -> str:
    """スコアに基づいてマッチング理由を自動生成"""
    reasons = []

    # スコアが高い項目を優先的に理由に含める
    if scores["市場ソリューションフィット"] >= 15:
        # 強みと課題の補完性
        a_strengths = a.get("全強み", [])
        b_issues = b.get("全課題", [])
        if a_strengths and b_issues:
            strength_sample = a_strengths[0] if a_strengths else ""
            reasons.append(f"{strength_sample}による課題解決")

    if scores["バリューチェーン接続性"] >= 15:
        # ポジション補完性
        a_positions = a.get("全ポジション", [])
        b_positions = b.get("全ポジション", [])
        if a_positions and b_positions:
            reasons.append(f"{a_positions[0]}×{b_positions[0]}の相補性")

    if scores["対象市場一致度"] >= 10:
        # 対象業界の一致
        a_industries = a.get("全対象業界", set())
        b_industries = b.get("全対象業界", set())
        overlap = a_industries & b_industries
        if overlap:
            industry_sample = list(overlap)[0]
            reasons.append(f"{industry_sample}市場での協業可能性")

    if scores["事業拡張ポテンシャル"] >= 10:
        reasons.append("新市場開拓の可能性")

    a_phase = a.get("事業フェーズ", "")
    b_phase = b.get("事業フェーズ", "")
    if a_phase and b_phase and a_phase == b_phase:
        reasons.append(f"同じ{a_phase}での相互サポート")

    a_industry = a.get("業種カテゴリ", "")
    b_industry = b.get("業種カテゴリ", "")
    if a_industry != b_industry and a_industry and b_industry:
        reasons.append(f"{a_industry}と{b_industry}の異業種連携")

    # 複数の理由を組み合わせ
    reason = " × ".join(reasons) if reasons else "複合的なシナジー"
    return reason[:150]


def _generate_intro(match: dict) -> str:
    """紹介文を生成（API不使用・テンプレート版）"""
    a = match["メンバーA"]
    b = match["メンバーB"]
    # Claude API不使用 → フォールバック版のみ使用
    return _generate_fallback_intro(a, b, match)


def _generate_fallback_intro(a: dict, b: dict, match: dict) -> str:
    """Claude API不可時のフォールバック紹介文"""
    a_name = a.get('名前', '【名前未設定】')
    b_name = b.get('名前', '【名前未設定】')
    a_company = a.get('会社名', '')
    b_company = b.get('会社名', '')
    a_industry = a.get('業種カテゴリ', '')
    b_industry = b.get('業種カテゴリ', '')
    reason = match.get('マッチング理由', '')

    intro = f"""{a_name}さん・{b_name}さん、はじめまして！

Blendy Inc. のコーディネーターです。

このたび、おふたりを一度ご紹介させていただきたくご連絡いたしました。

{a_name}さんは {a_company} ({a_industry}) でご活動されており、{b_name}さんは {b_company} ({b_industry}) でご活動されています。

このマッチング理由として、{reason} という点が挙げられます。

おふたりの組み合わせは相性が良いと考えられます。まずはお互い簡単に自己紹介していただけますか？
"""
    return intro.strip()


def _select_balanced_pairs(scored: list[dict], max_count: int) -> list[dict]:
    """
    1人1件のマッチングに限定
    同一人物は最大1回まで（繋いでない人がいる状況を作る）
    """
    selected = []
    name_count: dict[str, int] = {}
    for match in scored:
        if len(selected) >= max_count:
            break
        a_name = match["メンバーA名"]
        b_name = match["メンバーB名"]
        if name_count.get(a_name, 0) < 1 and name_count.get(b_name, 0) < 1:
            selected.append(match)
            name_count[a_name] = name_count.get(a_name, 0) + 1
            name_count[b_name] = name_count.get(b_name, 0) + 1
    return selected


def save_backup(matches: list[dict], session_name: str = "", debug_log: list = None) -> str:
    """
    マッチング結果をローカルにバックアップ

    Args:
        matches: マッチング結果のリスト
        session_name: セッション名（例："2026年6月 第1回"）
        debug_log: デバッグログのリスト（失敗時やエラーログ用）

    Returns:
        バックアップファイルのパス
    """
    if debug_log is None:
        debug_log = []

    # backups ディレクトリを確保（プロジェクトルート直下に作成）
    # このモジュールは src/blendy/ 配下にあるため、2階層上がプロジェクトルート
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backup_dir = os.path.join(project_root, "backups")

    # デバッグ: どこに保存しようとしているかログ出力
    logger.debug(f"[BACKUP DEBUG] Project root: {project_root}")
    logger.debug(f"[BACKUP DEBUG] Backup dir: {backup_dir}")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logger.info(f"[BACKUP] Created backup directory: {backup_dir}/")

    # ファイル名：日付_セッション番号
    timestamp = datetime.now().strftime("%Y-%m-%d")
    session_counter = 1
    while True:
        filename = f"matching_results_{timestamp}_session{session_counter}.json"
        filepath = os.path.join(backup_dir, filename)
        if not os.path.exists(filepath):
            break
        session_counter += 1

    # マッチング結果をバックアップ用に整形（メンバーA/Bオブジェクトは除外）
    backup_matches = []
    for match in matches:
        backup_match = {
            "メンバーA名": match["メンバーA名"],
            "メンバーB名": match["メンバーB名"],
            "スコア": match["スコア"],
            "内訳": match["内訳"],
            "協業タイプ": match["協業タイプ"],
            "マッチング理由": match["マッチング理由"],
            "紹介文": match.get("紹介文", ""),
        }
        backup_matches.append(backup_match)

    # JSONで保存
    backup_data = {
        "session_name": session_name,
        "backup_timestamp": datetime.now().isoformat(),
        "total_matches": len(backup_matches),
        "matches": backup_matches,
        "debug_log": debug_log,  # デバッグログを含める
    }

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        logger.info(f"[BACKUP] Saved: {filepath}")
    except Exception as e:
        logger.error(f"[BACKUP ERROR] {e}")
        raise

    return filepath

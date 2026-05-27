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
from config import CLAUDE_API_KEY, MIN_SCORE, MAX_MATCHES_PER_RUN, COLLABORATION_TYPES

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

    # ── Step2: ルールベーススコアリング ───────────────────
    logger.info(f"  → {len(valid_pairs)}組をスコアリング中...")
    scored = []
    for a, b in valid_pairs:
        result = _score_pair_rules(a, b)
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


def _has_strength_keyword(member: dict, keywords: list[str]) -> bool:
    """
    強みのキーワードを判定（チェックボックス優先 + フォールバック）

    新フォーム: 強み_キーワード (checkbox array)
    旧フォーム: 強み (free-text)
    """
    # 新フォーム: チェックボックス配列を確認
    strength_keywords = member.get("強み_キーワード", [])
    if strength_keywords:
        # リストの場合
        if isinstance(strength_keywords, list):
            return any(kw in strength_keywords for kw in keywords)
        # 文字列の場合（フォールバック）
        return any(kw in strength_keywords for kw in keywords)

    # フォールバック: テキストフィールドをキーワード検索
    strength_text = member.get("強み", "")
    # キーワードマッピング（新フォーム → テキスト検索キーワード）
    keyword_map = {
        "技術・開発": ["開発", "技術", "ノウハウ", "システム", "設計", "クリエイティブ", "AI", "実装"],
        "営業・ネットワーク": ["営業", "ネットワーク", "顧客", "チャネル", "実績", "人脈", "営業力"],
    }

    for keyword in keywords:
        search_terms = keyword_map.get(keyword, [keyword])
        if any(term in strength_text for term in search_terms):
            return True

    return False


def _has_gap_keyword(member: dict, keywords: list[str]) -> bool:
    """
    課題のキーワードを判定（チェックボックス優先 + フォールバック）

    新フォーム: 課題_キーワード (checkbox array)
    旧フォーム: 課題・足りないもの (free-text)
    """
    # 新フォーム: チェックボックス配列を確認
    gap_keywords = member.get("課題_キーワード", [])
    if gap_keywords:
        # リストの場合
        if isinstance(gap_keywords, list):
            return any(kw in gap_keywords for kw in keywords)
        # 文字列の場合（フォールバック）
        return any(kw in gap_keywords for kw in keywords)

    # フォールバック: テキストフィールドをキーワード検索
    gap_text = member.get("課題・足りないもの", "")
    # キーワードマッピング（新フォーム → テキスト検索キーワード）
    keyword_map = {
        "営業・マーケティング": ["営業", "マーケティング", "集客"],
        "営業ネットワーク": ["営業", "ネットワーク", "顧客", "営業人材"],
        "技術・開発": ["開発", "技術", "システム", "実装", "エンジニア"],
    }

    for keyword in keywords:
        search_terms = keyword_map.get(keyword, [keyword])
        if any(term in gap_text for term in search_terms):
            return True

    return False


def _calc_client_fit(a: dict, b: dict) -> int:
    """エンドクライアント一致度（30点満点）"""
    score = 0

    # 業界一致（完全一致 +15, 類似 +8）
    industry_a = a.get("エンドクライアント業界", "")
    industry_b = b.get("エンドクライアント業界", "")
    if industry_a == industry_b:
        score += 15
    elif any(kw in industry_a for kw in ["IT", "SaaS", "テック"]) and \
         any(kw in industry_b for kw in ["IT", "SaaS", "テック"]):
        score += 8  # 同じカテゴリ
    elif industry_a and industry_b:
        score += 3  # 異業種でも存在

    # 規模一致
    if a.get("エンドクライアント規模") == b.get("エンドクライアント規模"):
        score += 10
    elif {a.get("エンドクライアント規模"), b.get("エンドクライアント規模")} == {"スタートアップ", "中堅企業"}:
        score += 5  # 段階的成長に対応

    # 課題一致
    if a.get("クライアントの課題") == b.get("クライアントの課題"):
        score += 5

    return min(score, 30)


def _calc_chain_fit(a: dict, b: dict) -> int:
    """バリューチェーン接続性（25点満点）"""
    chain_a = a.get("バリューチェーン位置", [])
    chain_b = b.get("バリューチェーン位置", [])

    if not chain_a or not chain_b:
        return 0

    min_distance = 100
    for pos_a in chain_a:
        for pos_b in chain_b:
            if pos_a in VALUE_CHAIN_ORDER and pos_b in VALUE_CHAIN_ORDER:
                idx_a = VALUE_CHAIN_ORDER.index(pos_a)
                idx_b = VALUE_CHAIN_ORDER.index(pos_b)
                distance = abs(idx_a - idx_b)
                min_distance = min(min_distance, distance)

    if min_distance == 1:
        return 25  # 隣同士
    elif min_distance == 2:
        return 15  # 2つ隣
    elif min_distance == 3:
        return 8   # 3つ隣
    elif min_distance == 0:
        return 0   # 同じ工程
    else:
        return 0


def _calc_market_fit(a: dict, b: dict) -> int:
    """市場ソリューションフィット（25点満点）"""
    # 強みのキーワード判定（チェックボックス優先 + フォールバック）
    a_has_solution = _has_strength_keyword(a, ["技術・開発"])
    b_has_solution = _has_strength_keyword(b, ["技術・開発"])

    a_has_market = _has_strength_keyword(a, ["営業・ネットワーク"])
    b_has_market = _has_strength_keyword(b, ["営業・ネットワーク"])

    # 課題のキーワード判定（チェックボックス優先 + フォールバック）
    a_needs_market = _has_gap_keyword(a, ["営業・マーケティング", "営業ネットワーク"])
    b_needs_market = _has_gap_keyword(b, ["営業・マーケティング", "営業ネットワーク"])

    a_needs_solution = _has_gap_keyword(a, ["技術・開発"])
    b_needs_solution = _has_gap_keyword(b, ["技術・開発"])

    # 補完性判定（より柔軟に）
    # パターン1: 完全補完（一方が強みで他方が課題）
    if (a_has_solution and b_needs_solution and a_needs_market and b_has_market) or \
       (b_has_solution and a_needs_solution and b_needs_market and a_has_market):
        return 25

    # パターン2: ソリューション × 市場の直接補完
    if (a_has_solution and b_has_market) or (b_has_solution and a_has_market):
        return 20

    # パターン3: 部分的な補完
    if ((a_has_solution or a_has_market) and (b_has_solution or b_has_market)):
        return 10

    return 0


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
    """
    対象市場一致度（15点満点）

    Phase 1 追加：マルチアクティビティ対応
    両社が狙っている対象業界の共通部分を計算

    例）
    A社：対象業界=「医療」「バイオ」
    B社：対象業界=「医療」「研究機関」
    → 共通「医療」 = 1個 / max(2,2) = 50% → 7.5点
    """
    score = 0

    # 対象業界を取得（マルチアクティビティ対応）
    # マルチアクティビティ: 「対象業界」フィールド
    # シングルアクティビティ: 「エンドクライアント業界」フィールド（フォールバック）
    target_industries_a = _parse_industries(a.get("対象業界", "") or a.get("エンドクライアント業界", ""))
    target_industries_b = _parse_industries(b.get("対象業界", "") or b.get("エンドクライアント業界", ""))

    if not target_industries_a or not target_industries_b:
        return 0  # 対象業界が未設定の場合はスコアなし

    # 共通業界を検出
    common_industries = set(target_industries_a) & set(target_industries_b)

    if not common_industries:
        return 0  # 共通業界がない

    # スコア計算：共通業界の割合 × 最大15点
    overlap_ratio = len(common_industries) / max(len(target_industries_a), len(target_industries_b))
    score = int(overlap_ratio * 15)

    logger.debug(f"対象市場一致度: {a['名前']} × {b['名前']}")
    logger.debug(f"  A: {target_industries_a}, B: {target_industries_b}")
    logger.debug(f"  共通: {list(common_industries)}, スコア: {score}")

    return min(score, 15)


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

    if scores["エンドクライアント一致度"] >= 15:
        reasons.append(f"同じ{a.get('エンドクライアント業界')}向け市場")

    if scores["バリューチェーン接続性"] >= 15:
        reasons.append("バリューチェーンで連携可能")

    if scores["市場ソリューションフィット"] >= 15:
        reasons.append(f"{a.get('名前')}のソリューションと{b.get('名前')}の市場を補完")

    if scores["対象市場一致度"] >= 7:
        # 共通の対象業界を抽出して表示
        industries_a = _parse_industries(a.get("対象業界", "") or a.get("エンドクライアント業界", ""))
        industries_b = _parse_industries(b.get("対象業界", "") or b.get("エンドクライアント業界", ""))
        common = set(industries_a) & set(industries_b)
        if common:
            industry_text = "・".join(list(common)[:2])  # 最大2つまで表示
            reasons.append(f"同じ{industry_text}市場を対象")

    if scores["事業拡張ポテンシャル"] >= 10:
        reasons.append("新市場開拓の可能性")

    reason = " + ".join(reasons) if reasons else "複合的なシナジー"
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
    a_service = a.get('主力サービス', '')
    b_service = b.get('主力サービス', '')
    a_strength = a.get('強み', '')
    b_strength = b.get('強み', '')
    a_issue = a.get('課題・足りないもの', '')
    b_issue = b.get('課題・足りないもの', '')
    reason = match.get('マッチング理由', '')

    intro = f"""{a_name}さん・{b_name}さん、はじめまして！

Blendy Inc. のコーディネーターです。

このたび、おふたりを一度ご紹介させていただきたくご連絡いたしました。

{a_name}さんは {a_service} を提供されており、{a_strength} という強みをお持ちです。一方で {a_issue} という課題をお持ちと伺っています。

{b_name}さんは {b_service} を提供されており、{b_strength} という強みをお持ちです。一方で {b_issue} という課題をお持ちと伺っています。

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

    # backups ディレクトリを確保（スクリプトと同じディレクトリに作成）
    # プロジェクトルートディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backup_dir = os.path.join(script_dir, "backups")

    # デバッグ: どこに保存しようとしているかログ出力
    logger.debug(f"[BACKUP DEBUG] Script dir: {script_dir}")
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

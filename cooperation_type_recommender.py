"""
協業タイプ自動推測エンジン
課題感・強み・バリューチェーン位置から、最適な協業タイプを推奨する
"""

from typing import List, Dict, Tuple

# 協業タイプの定義
COOPERATION_TYPES = {
    "A型": "バリューチェーン型（営業 × 導入・サポート）",
    "B型": "市場参入型（サービス × 営業チャネル）",
    "C型": "バンドル強化型（営業 × マーケティング）",
    "D型": "OEM・裏方型（フロント × バックエンド）",
    "E型": "相互紹介型（クライアント紹介し合う）",
    "F型": "共同開発型（一緒に新サービスを作る）",
    "G型": "リソース補完型（人員・キャパをシェア）",
}


def infer_cooperation_type(
    challenges: List[str],
    strengths: List[str],
    value_chain_positions: List[str],
    business_phase: str,
    service_content: str,
) -> Tuple[str, Dict[str, float], str]:
    """
    課題感、強み、バリューチェーン位置から協業タイプを推測

    Args:
        challenges: 課題キーワードのリスト（例：["営業・マーケティング", "技術・開発"]）
        strengths: 強みキーワードのリスト（例：["技術・開発", "業界知見"]）
        value_chain_positions: バリューチェーン位置（複数選択）
        business_phase: 事業フェーズ（例：「成長期」）
        service_content: 主力サービス・事業内容（テキスト）

    Returns:
        (推奨協業タイプ, スコア辞書, 推奨理由)
    """

    scores = {type_name: 0.0 for type_name in COOPERATION_TYPES.keys()}
    reasoning = []

    # ===== スコアリングロジック =====

    # 1. 課題感からのスコア（各協業タイプが補完する課題を検出）
    if "営業・マーケティング" in challenges:
        # 営業力が足りない → B型、C型が活躍
        scores["B型"] += 30
        scores["C型"] += 25
        scores["E型"] += 15
        reasoning.append("営業・マーケティング力が課題のため、営業支援型が推奨")

    if "技術・開発" in challenges:
        # 開発力が足りない → D型、F型が活躍
        scores["D型"] += 30
        scores["F型"] += 25
        scores["G型"] += 15
        reasoning.append("技術開発力が課題のため、技術協業型が推奨")

    if "営業ネットワーク" in challenges:
        # ネットワークが足りない → A型、E型が活躍
        scores["A型"] += 25
        scores["E型"] += 30
        scores["B型"] += 20
        reasoning.append("営業ネットワークが課題のため、紹介型が推奨")

    if "資金・リソース" in challenges:
        # リソースが足りない → G型が活躍
        scores["G型"] += 35
        scores["B型"] += 10
        reasoning.append("人材・リソースが課題のため、リソース補完型が推奨")

    if "業界知見" in challenges:
        # 業界知見がない → A型、E型が補完
        scores["A型"] += 20
        scores["E型"] += 15
        scores["C型"] += 10
        reasoning.append("業界知見が課題のため、経験者パートナー型が推奨")

    # 2. 強みからのスコア（各協業タイプで活躍できる強みを検出）
    if "技術・開発" in strengths:
        # 技術力がある → D型、F型での貢献可能
        scores["D型"] += 25
        scores["F型"] += 30
        scores["A型"] += 10
        reasoning.append("技術開発力が強みのため、開発パートナー型での協業が最適")

    if "営業・ネットワーク" in strengths:
        # 営業力がある → A型、B型、E型での貢献可能
        scores["A型"] += 30
        scores["B型"] += 20
        scores["E型"] += 25
        reasoning.append("営業ネットワークが強みのため、営業支援型での協業が最適")

    if "業界知見" in strengths:
        # 業界知見がある → A型、E型での貢献可能
        scores["A型"] += 20
        scores["E型"] += 25
        scores["C型"] += 15
        reasoning.append("業界知見が強みのため、業界特化型での協業が最適")

    if "ブランド" in strengths:
        # ブランド力がある → C型（バンドル強化）、E型（相互紹介）
        scores["C型"] += 25
        scores["E型"] += 20
        scores["B型"] += 15
        reasoning.append("ブランド・認知度が強みのため、共販・バンドル型が最適")

    if "コンテンツ" in strengths:
        # コンテンツがある → C型（マーケティング）、F型（新サービス開発）
        scores["C型"] += 20
        scores["F型"] += 15
        scores["E型"] += 10
        reasoning.append("コンテンツ資産が強みのため、マーケティング連携型が最適")

    # 3. バリューチェーン位置からのスコア
    if "営業・提案・クロージング" in value_chain_positions:
        # 営業機能が強い → A型、B型、C型、E型
        scores["A型"] += 15
        scores["B型"] += 20
        scores["C型"] += 15
        scores["E型"] += 15

    if "制作・開発・導入" in value_chain_positions:
        # 開発・導入機能が強い → A型（導入サポート）、D型、F型
        scores["A型"] += 15
        scores["D型"] += 20
        scores["F型"] += 20

    if "認知・ブランディング" in value_chain_positions:
        # ブランディング機能が強い → C型、E型
        scores["C型"] += 20
        scores["E型"] += 15

    if "集客・マーケティング" in value_chain_positions:
        # マーケティング機能が強い → B型、C型
        scores["B型"] += 20
        scores["C型"] += 25

    # 4. 事業フェーズからの調整
    if business_phase in ["アイデア段階", "立上げ期"]:
        # 初期段階 → リソース補完（G型）、共同開発（F型）が重要
        scores["G型"] += 15
        scores["F型"] += 10

    elif business_phase == "成長期":
        # 成長期 → 営業支援（A型、B型）、マーケティング（C型）が重要
        scores["A型"] += 10
        scores["B型"] += 15
        scores["C型"] += 10

    # 5. テキスト分析（簡易版）
    keywords_by_type = {
        "A型": ["導入", "サポート", "実装"],
        "B型": ["チャネル", "営業", "拡販"],
        "C型": ["マーケティング", "ブランド", "バンドル"],
        "D型": ["OEM", "裏方", "バックエンド"],
        "E型": ["紹介", "アライアンス", "顧客共有"],
        "F型": ["共同開発", "新サービス", "協働"],
        "G型": ["人材", "リソース", "キャパ"],
    }

    service_text = service_content.lower()
    for type_name, keywords in keywords_by_type.items():
        for keyword in keywords:
            if keyword.lower() in service_text:
                scores[type_name] += 5

    # ===== 推奨タイプ決定 =====
    recommended_type = max(scores, key=scores.get)
    max_score = scores[recommended_type]

    # スコアが低い場合は「確信度が低い」を示す
    reasoning_text = " | ".join(reasoning) if reasoning else "標準マッチング"

    if max_score < 20:
        reasoning_text += " ⚠️ 確信度が低いため、複数パターンの検討をお勧めします"

    return recommended_type, scores, reasoning_text


def get_cooperation_type_description(type_name: str) -> str:
    """協業タイプの説明を取得"""
    return COOPERATION_TYPES.get(type_name, "不明")


if __name__ == "__main__":
    # テスト実行
    challenges = ["営業・マーケティング", "資金・リソース"]
    strengths = ["技術・開発", "業界知見"]
    value_chain = ["制作・開発・導入", "営業・提案・クロージング"]
    phase = "成長期"
    service = "SaaS型の営業支援ツール。中小企業向けに導入から継続支援を行う。"

    recommended, scores, reasoning = infer_cooperation_type(
        challenges, strengths, value_chain, phase, service
    )

    print(f"推奨協業タイプ: {recommended} ({get_cooperation_type_description(recommended)})")
    print(f"理由: {reasoning}")
    print("\nスコア詳細:")
    for type_name, score in sorted(scores.items(), key=lambda x: -x[1]):
        print(f"  {type_name}: {score:.1f}")

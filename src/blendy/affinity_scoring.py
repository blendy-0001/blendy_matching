"""レベル2/3 親和性スコアリング（叩き）

方向性ドキュメントの「新たに必要なスコアリング項目」を Rule-based で実装する。
既存の L1 ルールスコア(100点)に対する **加算層(上限50点)** として機能する。

設計上の非対称（方向性ドキュメントに忠実）:
- 施策・時間軸・協調 = 揃うほど高得点（類似性）
- 意思決定スタイル   = 逆ほど高得点（相補性。即決派 × 慎重派 = 成功パターン）
- ビジョン自由記述   = Phase1 では非採点（Phase2 で Claude 抽出）

すべて純粋関数。Notion / Claude / I/O に依存しないため単体テスト可能。
"""
from __future__ import annotations

from pydantic import BaseModel

from .profile_schema import (
    AffinityProfile,
    COLLAB_ORDER,
    DECISION_ORDER,
    PAST_LEVEL,
    TIME_ORDER,
    from_member_dict,
)

# 加算層の配点（叩きの初期値。実データで調整する前提）
SCORE_WEIGHTS_AFFINITY = {
    "施策親和性(活動重複度)": 12,
    "意思決定スタイル相補性": 12,
    "価値観親和性(時間軸)": 10,
    "コミットレベル一致": 8,
    "協調スタイル親和性": 5,
    "協業経験ボーナス": 3,
}
AFFINITY_MAX = sum(SCORE_WEIGHTS_AFFINITY.values())  # 50


class AffinityItem(BaseModel):
    label: str
    score: float
    max_score: float
    note: str


class AffinityBreakdown(BaseModel):
    total: float
    items: list[AffinityItem]
    reasons: list[str]


def _round1(x: float) -> float:
    return round(x + 1e-9, 1)


# ────────────────────────────────────────────
# 各次元の純粋関数（戻り値: (score, note)）
# ────────────────────────────────────────────
def score_activity_affinity(a: AffinityProfile, b: AffinityProfile) -> tuple[float, str]:
    """L2: 施策セットの Jaccard 類似度 × 12（揃うほど高）"""
    max_pts = SCORE_WEIGHTS_AFFINITY["施策親和性(活動重複度)"]
    set_a = {x.strip().lower() for x in a.activities if x.strip()}
    set_b = {x.strip().lower() for x in b.activities if x.strip()}
    if not set_a or not set_b:
        return 0.0, "施策データ不足"
    inter = set_a & set_b
    union = set_a | set_b
    jaccard = len(inter) / len(union)
    score = _round1(jaccard * max_pts)
    note = f"共通施策 {len(inter)}/{len(union)} (Jaccard {jaccard:.2f})"
    return score, note


def score_decision_complementarity(a: AffinityProfile, b: AffinityProfile) -> tuple[float, str]:
    """L3: 意思決定スタイルの相補性（即決↔慎重=満点、同一=0）"""
    max_pts = SCORE_WEIGHTS_AFFINITY["意思決定スタイル相補性"]
    if a.decision_style is None or b.decision_style is None:
        return 0.0, "意思決定スタイル データ不足"
    distance = abs(DECISION_ORDER[a.decision_style] - DECISION_ORDER[b.decision_style])  # 0..2
    score = _round1(distance / 2 * max_pts)
    if distance == 2:
        note = f"{a.decision_style.value} × {b.decision_style.value} → 相補的(高評価)"
    elif distance == 0:
        note = f"両者 {a.decision_style.value} → 相補性なし"
    else:
        note = f"{a.decision_style.value} × {b.decision_style.value} → やや相補的"
    return score, note


def score_time_horizon_affinity(a: AffinityProfile, b: AffinityProfile) -> tuple[float, str]:
    """L3: 時間軸の親和性（同一=満点、両端=0）"""
    max_pts = SCORE_WEIGHTS_AFFINITY["価値観親和性(時間軸)"]
    if a.time_horizon is None or b.time_horizon is None:
        return 0.0, "時間軸 データ不足"
    distance = abs(TIME_ORDER[a.time_horizon] - TIME_ORDER[b.time_horizon])  # 0..2
    score = _round1((1 - distance / 2) * max_pts)
    if distance == 0:
        note = f"両者 {a.time_horizon.value}視点 → 価値観が揃う"
    elif distance == 2:
        note = f"{a.time_horizon.value} × {b.time_horizon.value} → 時間軸が乖離"
    else:
        note = f"{a.time_horizon.value} × {b.time_horizon.value} → 概ね近い"
    return score, note


def score_commitment_match(a: AffinityProfile, b: AffinityProfile) -> tuple[float, str]:
    """L3: コミット度(本気度)の近さ（差が小さいほど高）"""
    max_pts = SCORE_WEIGHTS_AFFINITY["コミットレベル一致"]
    if a.commitment_level is None or b.commitment_level is None:
        return 0.0, "コミットレベル データ不足"
    diff = abs(a.commitment_level - b.commitment_level)  # 0..4
    score = _round1(max(max_pts - diff * 2, 0))
    note = f"本気度 {a.commitment_level} × {b.commitment_level} (差 {diff})"
    return score, note


def score_collaboration_affinity(a: AffinityProfile, b: AffinityProfile) -> tuple[float, str]:
    """L3: 協調スタイルの親和性（近いほど高）"""
    max_pts = SCORE_WEIGHTS_AFFINITY["協調スタイル親和性"]
    if a.collaboration_style is None or b.collaboration_style is None:
        return 0.0, "協調スタイル データ不足"
    distance = abs(COLLAB_ORDER[a.collaboration_style] - COLLAB_ORDER[b.collaboration_style])  # 0..2
    score = _round1((1 - distance / 2) * max_pts)
    note = f"{a.collaboration_style.value} × {b.collaboration_style.value}"
    return score, note


def score_past_collaboration_bonus(a: AffinityProfile, b: AffinityProfile) -> tuple[float, str]:
    """L3: 協業経験ボーナス（経験豊富な側がいれば緩い相手とも成功しやすい）"""
    max_pts = SCORE_WEIGHTS_AFFINITY["協業経験ボーナス"]
    if a.past_collaboration is None and b.past_collaboration is None:
        return 0.0, "協業経験 データ不足"
    level = max(
        PAST_LEVEL.get(a.past_collaboration, 0),
        PAST_LEVEL.get(b.past_collaboration, 0),
    )  # 0..2
    score = _round1(level / 2 * max_pts)
    note = f"最大協業経験レベル {level}"
    return score, note


# 次元定義（label と関数の対応）
_DIMENSIONS = [
    ("施策親和性(活動重複度)", score_activity_affinity),
    ("意思決定スタイル相補性", score_decision_complementarity),
    ("価値観親和性(時間軸)", score_time_horizon_affinity),
    ("コミットレベル一致", score_commitment_match),
    ("協調スタイル親和性", score_collaboration_affinity),
    ("協業経験ボーナス", score_past_collaboration_bonus),
]


def compute_affinity(a: AffinityProfile, b: AffinityProfile) -> AffinityBreakdown:
    """L2/L3 の親和性を算出し、内訳と理由文を返す。"""
    items: list[AffinityItem] = []
    total = 0.0
    for label, fn in _DIMENSIONS:
        score, note = fn(a, b)
        max_pts = SCORE_WEIGHTS_AFFINITY[label]
        items.append(AffinityItem(label=label, score=score, max_score=max_pts, note=note))
        total += score

    reasons = _build_reasons(items)
    return AffinityBreakdown(total=_round1(total), items=items, reasons=reasons)


def compute_affinity_from_members(a: dict, b: dict) -> AffinityBreakdown:
    """Notion 由来のメンバー dict を受け取り、親和性を算出する（結線用ヘルパー）。"""
    return compute_affinity(from_member_dict(a), from_member_dict(b))


def _build_reasons(items: list[AffinityItem]) -> list[str]:
    """「成功しそうな理由」を、高得点(満点の70%以上)の次元から自動生成する。"""
    reasons: list[str] = []
    for item in items:
        if item.max_score > 0 and item.score >= item.max_score * 0.7:
            reasons.append(f"{item.label}: {item.note}")
    return reasons

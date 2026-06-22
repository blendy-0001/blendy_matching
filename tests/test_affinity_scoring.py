"""affinity_scoring（L2/L3 親和性スコアリング）の単体テスト

純粋関数のため Notion / Claude 非依存で全網羅できる。
"""
import pytest

from blendy.affinity_scoring import (
    AFFINITY_MAX,
    SCORE_WEIGHTS_AFFINITY,
    compute_affinity,
    compute_affinity_from_members,
    score_activity_affinity,
    score_collaboration_affinity,
    score_commitment_match,
    score_decision_complementarity,
    score_past_collaboration_bonus,
    score_time_horizon_affinity,
)
from blendy.profile_schema import (
    AffinityProfile,
    CollaborationStyle,
    DecisionStyle,
    PastCollaboration,
    TimeHorizon,
)


def P(**kwargs) -> AffinityProfile:
    return AffinityProfile(**kwargs)


# ── 施策親和性（類似性: 揃うほど高） ──────────────
def test_activity_full_overlap_is_max():
    a = P(activities=["交流会", "登壇"])
    b = P(activities=["交流会", "登壇"])
    score, _ = score_activity_affinity(a, b)
    assert score == SCORE_WEIGHTS_AFFINITY["施策親和性(活動重複度)"]


def test_activity_no_overlap_is_zero():
    a = P(activities=["交流会"])
    b = P(activities=["SNS発信"])
    score, _ = score_activity_affinity(a, b)
    assert score == 0.0


def test_activity_partial_overlap_jaccard():
    a = P(activities=["交流会", "登壇"])
    b = P(activities=["交流会", "SNS発信"])
    # Jaccard = 1/3 → 12 * 1/3 = 4.0
    score, _ = score_activity_affinity(a, b)
    assert score == 4.0


def test_activity_empty_is_zero_and_no_error():
    score, note = score_activity_affinity(P(), P(activities=["交流会"]))
    assert score == 0.0
    assert "データ不足" in note


# ── 意思決定スタイル（相補性: 逆ほど高） ──────────────
def test_decision_complementary_is_max():
    a = P(decision_style=DecisionStyle.即決派)
    b = P(decision_style=DecisionStyle.慎重派)
    score, _ = score_decision_complementarity(a, b)
    assert score == SCORE_WEIGHTS_AFFINITY["意思決定スタイル相補性"]


def test_decision_same_is_zero():
    a = P(decision_style=DecisionStyle.即決派)
    b = P(decision_style=DecisionStyle.即決派)
    score, _ = score_decision_complementarity(a, b)
    assert score == 0.0


def test_decision_adjacent_is_half():
    a = P(decision_style=DecisionStyle.即決派)
    b = P(decision_style=DecisionStyle.バランス型)
    score, _ = score_decision_complementarity(a, b)
    assert score == 6.0  # 距離1 → 12 * 1/2


def test_decision_missing_is_zero():
    score, note = score_decision_complementarity(P(), P(decision_style=DecisionStyle.即決派))
    assert score == 0.0
    assert "データ不足" in note


# ── 時間軸（親和性: 揃うほど高） ──────────────
def test_time_horizon_same_is_max():
    a = P(time_horizon=TimeHorizon.長期)
    b = P(time_horizon=TimeHorizon.長期)
    score, _ = score_time_horizon_affinity(a, b)
    assert score == SCORE_WEIGHTS_AFFINITY["価値観親和性(時間軸)"]


def test_time_horizon_opposite_is_zero():
    a = P(time_horizon=TimeHorizon.長期)
    b = P(time_horizon=TimeHorizon.短期)
    score, _ = score_time_horizon_affinity(a, b)
    assert score == 0.0


# ── コミットレベル（近さ） ──────────────
def test_commitment_same_is_max():
    score, _ = score_commitment_match(P(commitment_level=5), P(commitment_level=5))
    assert score == SCORE_WEIGHTS_AFFINITY["コミットレベル一致"]


def test_commitment_far_is_zero():
    # 差4 → 8 - 4*2 = 0
    score, _ = score_commitment_match(P(commitment_level=1), P(commitment_level=5))
    assert score == 0.0


def test_commitment_diff_one():
    score, _ = score_commitment_match(P(commitment_level=3), P(commitment_level=4))
    assert score == 6.0  # 8 - 1*2


# ── 協調スタイル（親和性） ──────────────
def test_collaboration_same_is_max():
    a = P(collaboration_style=CollaborationStyle.協調志向)
    b = P(collaboration_style=CollaborationStyle.協調志向)
    score, _ = score_collaboration_affinity(a, b)
    assert score == SCORE_WEIGHTS_AFFINITY["協調スタイル親和性"]


def test_collaboration_opposite_is_zero():
    a = P(collaboration_style=CollaborationStyle.個人主義)
    b = P(collaboration_style=CollaborationStyle.協調志向)
    score, _ = score_collaboration_affinity(a, b)
    assert score == 0.0


# ── 協業経験ボーナス ──────────────
def test_past_collaboration_levels():
    assert score_past_collaboration_bonus(P(past_collaboration=PastCollaboration.なし),
                                          P(past_collaboration=PastCollaboration.なし))[0] == 0.0
    assert score_past_collaboration_bonus(P(past_collaboration=PastCollaboration.三回以上),
                                          P(past_collaboration=PastCollaboration.なし))[0] == 3.0
    assert score_past_collaboration_bonus(P(past_collaboration=PastCollaboration.一_二回),
                                          P(past_collaboration=PastCollaboration.なし))[0] == 1.5


# ── 合計・不変条件 ──────────────
def test_compute_affinity_full_profiles_within_bounds():
    a = P(
        activities=["交流会", "登壇"],
        decision_style=DecisionStyle.即決派,
        time_horizon=TimeHorizon.長期,
        commitment_level=5,
        collaboration_style=CollaborationStyle.協調志向,
        past_collaboration=PastCollaboration.三回以上,
    )
    b = P(
        activities=["交流会", "登壇"],
        decision_style=DecisionStyle.慎重派,
        time_horizon=TimeHorizon.長期,
        commitment_level=5,
        collaboration_style=CollaborationStyle.協調志向,
        past_collaboration=PastCollaboration.なし,
    )
    bd = compute_affinity(a, b)
    assert 0 <= bd.total <= AFFINITY_MAX
    assert AFFINITY_MAX == 50
    for item in bd.items:
        assert item.score <= item.max_score
    # この理想ペアは満点になるはず（施策一致, 意思決定相補, 時間軸一致, コミット一致, 協調一致, 経験あり）
    assert bd.total == AFFINITY_MAX
    assert bd.reasons  # 理由文が生成される


def test_compute_affinity_all_missing_is_zero():
    bd = compute_affinity(P(), P())
    assert bd.total == 0.0
    assert bd.reasons == []
    assert len(bd.items) == len(SCORE_WEIGHTS_AFFINITY)


# ── dict 経由（防御的パース） ──────────────
def test_compute_from_members_defensive_parsing():
    a = {
        "名前": "A社",
        "施策活動": ["交流会"],
        "意思決定スタイル": "即決派",
        "時間軸": "長期",
        "コミットレベル": "4",          # 文字列でも int に変換
        "協調スタイル": "不正な値",      # 不正 enum は None で継続
        "協業経験": "3回以上",
    }
    b = {
        "名前": "B社",
        "施策活動": "交流会、SNS発信",   # 文字列(区切り)でも分解
        "意思決定スタイル": "慎重派",
        "時間軸": "短期",
        "コミットレベル": 5,
    }
    bd = compute_affinity_from_members(a, b)
    assert 0 <= bd.total <= AFFINITY_MAX
    # 協調スタイルは不正値→None→0点（例外を出さない）
    collab_item = next(i for i in bd.items if i.label == "協調スタイル親和性")
    assert collab_item.score == 0.0


def test_commitment_out_of_range_rejected():
    with pytest.raises(ValueError):
        AffinityProfile(commitment_level=7)

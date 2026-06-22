"""レベル2/3 プロファイルのデータ構造（叩き）

方向性ドキュメントの「マッチング品質を決める3階層」のうち、
- レベル2: 施策・種まき活動
- レベル3: 性格・価値観・意思決定スタイル
を構造化質問で取得するための型定義。

このモジュールは純粋（Notion / Claude 非依存）で、affinity_scoring から参照される。
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ────────────────────────────────────────────
# レベル3 の列挙（順序尺度。値は距離計算用のインデックス）
# ────────────────────────────────────────────
class DecisionStyle(str, Enum):
    """意思決定スタイル（即決 ↔ 慎重 の順序尺度）"""
    即決派 = "即決派"
    バランス型 = "バランス型"
    慎重派 = "慎重派"


class TimeHorizon(str, Enum):
    """時間軸（長期 ↔ 短期 の順序尺度）"""
    長期 = "長期"
    中期 = "中期"
    短期 = "短期"


class CollaborationStyle(str, Enum):
    """協調スタイル（個人主義 ↔ 協調志向 の順序尺度）"""
    個人主義 = "個人主義"
    バランス = "バランス"
    協調志向 = "協調志向"


class PastCollaboration(str, Enum):
    """過去の協業経験"""
    なし = "なし"
    一_二回 = "1-2回"
    三回以上 = "3回以上"


# 順序尺度 → インデックス（距離計算に使用）
DECISION_ORDER = {DecisionStyle.即決派: 0, DecisionStyle.バランス型: 1, DecisionStyle.慎重派: 2}
TIME_ORDER = {TimeHorizon.長期: 0, TimeHorizon.中期: 1, TimeHorizon.短期: 2}
COLLAB_ORDER = {CollaborationStyle.個人主義: 0, CollaborationStyle.バランス: 1, CollaborationStyle.協調志向: 2}
PAST_LEVEL = {PastCollaboration.なし: 0, PastCollaboration.一_二回: 1, PastCollaboration.三回以上: 2}


# ────────────────────────────────────────────
# レベル2/3 プロファイル
# ────────────────────────────────────────────
class AffinityProfile(BaseModel):
    """親和性スコアリングが参照する L2/L3 のサブセット。

    すべて Optional。旧フォーム経由で欠損していても例外を出さず、
    affinity_scoring 側で中立スコア(0)として扱う。
    """
    activities: list[str] = Field(default_factory=list, description="L2: 施策・種まき活動キーワード")
    decision_style: Optional[DecisionStyle] = Field(default=None, description="L3: 意思決定スタイル")
    time_horizon: Optional[TimeHorizon] = Field(default=None, description="L3: 時間軸")
    commitment_level: Optional[int] = Field(default=None, description="L3: コミット度(Likert 1-5)")
    collaboration_style: Optional[CollaborationStyle] = Field(default=None, description="L3: 協調スタイル")
    past_collaboration: Optional[PastCollaboration] = Field(default=None, description="L3: 協業経験")
    vision_text: str = Field(default="", description="L3: ビジョン・こだわり（Phase1では保存のみ・非採点）")

    @field_validator("commitment_level")
    @classmethod
    def _validate_commitment(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        if not 1 <= v <= 5:
            raise ValueError("commitment_level は 1〜5 の範囲で指定してください")
        return v


# メンバー dict（Notion 由来）で使う日本語フィールドキー
FIELD_ACTIVITIES = "施策活動"
FIELD_DECISION_STYLE = "意思決定スタイル"
FIELD_TIME_HORIZON = "時間軸"
FIELD_COMMITMENT = "コミットレベル"
FIELD_COLLAB_STYLE = "協調スタイル"
FIELD_PAST_COLLAB = "協業経験"
FIELD_VISION = "ビジョン記述"


def _coerce_enum(enum_cls, value):
    """値を enum に変換。不正/欠損なら None（防御的）。"""
    if value is None or value == "":
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None


def from_member_dict(member: dict) -> AffinityProfile:
    """Notion 由来のメンバー dict から AffinityProfile を防御的に構築する。

    欠損・型不一致でも例外を出さず、欠損フィールドは None / 空で返す。
    """
    raw_activities = member.get(FIELD_ACTIVITIES, []) or []
    if isinstance(raw_activities, str):
        # カンマ / 読点区切りの文字列にも一応対応
        raw_activities = [s.strip() for s in raw_activities.replace("、", ",").split(",") if s.strip()]
    activities = [str(a).strip() for a in raw_activities if str(a).strip()]

    commitment = member.get(FIELD_COMMITMENT)
    try:
        commitment = int(commitment) if commitment not in (None, "") else None
        if commitment is not None and not 1 <= commitment <= 5:
            commitment = None
    except (ValueError, TypeError):
        commitment = None

    return AffinityProfile(
        activities=activities,
        decision_style=_coerce_enum(DecisionStyle, member.get(FIELD_DECISION_STYLE)),
        time_horizon=_coerce_enum(TimeHorizon, member.get(FIELD_TIME_HORIZON)),
        commitment_level=commitment,
        collaboration_style=_coerce_enum(CollaborationStyle, member.get(FIELD_COLLAB_STYLE)),
        past_collaboration=_coerce_enum(PastCollaboration, member.get(FIELD_PAST_COLLAB)),
        vision_text=str(member.get(FIELD_VISION, "") or ""),
    )

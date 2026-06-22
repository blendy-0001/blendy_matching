"""Notion バックエンドの DataRepository 実装（Phase 0）

既存の notion_client 公開関数へ委譲するだけの薄いアダプタ。
挙動は従来と完全に同一。
"""
from __future__ import annotations

from .. import notion_client as nc
from .base import DataRepository


class NotionRepository(DataRepository):
    """notion_client へ委譲する実装。"""

    def get_all_members(self) -> list[dict]:
        return nc.get_all_members()

    def get_matched_pairs(self) -> set[frozenset]:
        return nc.get_matched_pairs()

    def get_stats(self) -> dict:
        return nc.get_stats()

    def get_activities_for_member(self, member_id: str, use_cache: bool = True) -> list[dict]:
        return nc.get_activities_for_member(member_id, use_cache=use_cache)

    def clear_activities_cache(self) -> None:
        return nc.clear_activities_cache()

    def create_member(self, data: dict) -> str:
        return nc.create_member(data)

    def create_activity(self, member_id: str, activity_data: dict) -> str:
        return nc.create_activity(member_id, activity_data)

    def save_matching_result(self, session_name: str, match: dict) -> str:
        return nc.save_matching_result(session_name, match)

    def save_to_history(self, match: dict):
        return nc.save_to_history(match)

    def save_unmatched_member(self, session_name: str, member: dict) -> str:
        return nc.save_unmatched_member(session_name, member)

    def save_error_log(
        self,
        error_type: str,
        error_message: str,
        analysis: str,
        affected_member: str = "",
        response_status: str = "未対応",
    ) -> bool:
        return nc.save_error_log(
            error_type, error_message, analysis,
            affected_member=affected_member, response_status=response_status,
        )

    def save_matching_analysis(
        self,
        session_name: str,
        matching_results: list[dict],
        statistics: dict,
    ) -> bool:
        return nc.save_matching_analysis(session_name, matching_results, statistics)

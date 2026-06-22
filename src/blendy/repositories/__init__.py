"""データアクセス層（Phase 0: Notion を Repository の裏に隠す）

アプリは `from .repositories import get_all_members, ...` のように、このパッケージ越しに
データへアクセスする。バックエンドは `DATA_BACKEND` で切替（既定 "notion"）。

将来 Postgres 実装を追加する際は、ここの `get_repository()` を差し替えるだけで済む。
cf. docs/architecture/target-architecture.md
"""
from __future__ import annotations

from .. import config
from .base import DataRepository
from .notion_repository import NotionRepository

_repository: DataRepository | None = None


def get_repository() -> DataRepository:
    """有効なバックエンドの DataRepository を返す（シングルトン）。"""
    global _repository
    if _repository is None:
        backend = getattr(config, "DATA_BACKEND", "notion").lower()
        if backend == "notion":
            _repository = NotionRepository()
        elif backend == "postgres":
            # Phase 1 で実装予定（target-architecture.md 参照）
            raise NotImplementedError("postgres backend は未実装です（Phase 1）")
        else:
            raise ValueError(f"未知の DATA_BACKEND: {backend}")
    return _repository


def set_repository(repo: DataRepository | None) -> None:
    """テスト用にバックエンドを差し替える / リセットする。"""
    global _repository
    _repository = repo


# ── モジュールレベルの委譲関数 ──────────────────────
# 既存の呼び出し側は import 元を notion_client → repositories に変えるだけでよい
# （呼び出し構文は不変）。
def get_all_members() -> list[dict]:
    return get_repository().get_all_members()


def get_matched_pairs() -> set[frozenset]:
    return get_repository().get_matched_pairs()


def get_stats() -> dict:
    return get_repository().get_stats()


def get_activities_for_member(member_id: str, use_cache: bool = True) -> list[dict]:
    return get_repository().get_activities_for_member(member_id, use_cache=use_cache)


def clear_activities_cache() -> None:
    return get_repository().clear_activities_cache()


def create_member(data: dict) -> str:
    return get_repository().create_member(data)


def create_activity(member_id: str, activity_data: dict) -> str:
    return get_repository().create_activity(member_id, activity_data)


def save_matching_result(session_name: str, match: dict) -> str:
    return get_repository().save_matching_result(session_name, match)


def save_to_history(match: dict):
    return get_repository().save_to_history(match)


def save_unmatched_member(session_name: str, member: dict) -> str:
    return get_repository().save_unmatched_member(session_name, member)


def save_error_log(
    error_type: str,
    error_message: str,
    analysis: str,
    affected_member: str = "",
    response_status: str = "未対応",
) -> bool:
    return get_repository().save_error_log(
        error_type, error_message, analysis,
        affected_member=affected_member, response_status=response_status,
    )


def save_matching_analysis(
    session_name: str,
    matching_results: list[dict],
    statistics: dict,
) -> bool:
    return get_repository().save_matching_analysis(session_name, matching_results, statistics)


__all__ = [
    "DataRepository", "NotionRepository", "get_repository", "set_repository",
    "get_all_members", "get_matched_pairs", "get_stats", "get_activities_for_member",
    "clear_activities_cache", "create_member", "create_activity", "save_matching_result",
    "save_to_history", "save_unmatched_member", "save_error_log", "save_matching_analysis",
]

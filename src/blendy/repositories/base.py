"""データアクセス層のインターフェース定義（Phase 0）

アプリ（main / matching_engine）はこのインターフェース越しにのみデータへアクセスし、
具体的なバックエンド（Notion / 将来の Postgres）に依存しない。

cf. docs/architecture/target-architecture.md
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class DataRepository(ABC):
    """メンバー / マッチング / ログのデータアクセス抽象。

    メソッドのシグネチャは既存 notion_client の公開関数と 1:1 に対応する。
    """

    # ── 読み取り ──
    @abstractmethod
    def get_all_members(self) -> list[dict]:
        ...

    @abstractmethod
    def get_matched_pairs(self) -> set[frozenset]:
        ...

    @abstractmethod
    def get_stats(self) -> dict:
        ...

    @abstractmethod
    def get_activities_for_member(self, member_id: str, use_cache: bool = True) -> list[dict]:
        ...

    @abstractmethod
    def clear_activities_cache(self) -> None:
        ...

    # ── 書き込み ──
    @abstractmethod
    def create_member(self, data: dict) -> str:
        ...

    @abstractmethod
    def create_activity(self, member_id: str, activity_data: dict) -> str:
        ...

    @abstractmethod
    def save_matching_result(self, session_name: str, match: dict) -> str:
        ...

    @abstractmethod
    def save_to_history(self, match: dict):
        ...

    @abstractmethod
    def save_unmatched_member(self, session_name: str, member: dict) -> str:
        ...

    @abstractmethod
    def save_error_log(
        self,
        error_type: str,
        error_message: str,
        analysis: str,
        affected_member: str = "",
        response_status: str = "未対応",
    ) -> bool:
        ...

    @abstractmethod
    def save_matching_analysis(
        self,
        session_name: str,
        matching_results: list[dict],
        statistics: dict,
    ) -> bool:
        ...

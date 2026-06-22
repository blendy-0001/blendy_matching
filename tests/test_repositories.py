"""データアクセス層（repositories）の単体テスト（Phase 0）

Notion へ実アクセスせず、ファクトリ・委譲・差し替えの挙動のみ検証する。
"""
import pytest

import blendy.repositories as repo_pkg
from blendy.repositories import get_repository, set_repository
from blendy.repositories.base import DataRepository
from blendy.repositories.notion_repository import NotionRepository


@pytest.fixture(autouse=True)
def _reset_singleton():
    """各テストの前後でシングルトンをリセット。"""
    set_repository(None)
    yield
    set_repository(None)


def test_default_backend_is_notion():
    assert isinstance(get_repository(), NotionRepository)


def test_get_repository_is_singleton():
    assert get_repository() is get_repository()


def test_unknown_backend_raises(monkeypatch):
    set_repository(None)
    monkeypatch.setattr(repo_pkg.config, "DATA_BACKEND", "mysql", raising=False)
    with pytest.raises(ValueError):
        get_repository()


def test_postgres_backend_not_implemented(monkeypatch):
    set_repository(None)
    monkeypatch.setattr(repo_pkg.config, "DATA_BACKEND", "postgres", raising=False)
    with pytest.raises(NotImplementedError):
        get_repository()


class FakeRepo(DataRepository):
    """委譲が正しく差し替えられることを確認する用のフェイク。"""
    def __init__(self):
        self.calls = []

    def get_all_members(self):
        self.calls.append("get_all_members")
        return [{"名前": "A社"}]

    def get_matched_pairs(self):
        return set()

    def get_stats(self):
        return {}

    def get_activities_for_member(self, member_id, use_cache=True):
        self.calls.append((member_id, use_cache))
        return []

    def clear_activities_cache(self):
        self.calls.append("clear")

    def create_member(self, data):
        self.calls.append(("create_member", data))
        return "page_123"

    def create_activity(self, member_id, activity_data):
        return "act_1"

    def save_matching_result(self, session_name, match):
        return "res_1"

    def save_to_history(self, match):
        return None

    def save_unmatched_member(self, session_name, member):
        return "unm_1"

    def save_error_log(self, error_type, error_message, analysis, affected_member="", response_status="未対応"):
        self.calls.append(("error", error_type, response_status))
        return True

    def save_matching_analysis(self, session_name, matching_results, statistics):
        return True


def test_module_functions_delegate_to_active_repository():
    fake = FakeRepo()
    set_repository(fake)

    assert repo_pkg.get_all_members() == [{"名前": "A社"}]
    assert repo_pkg.create_member({"名前": "X"}) == "page_123"
    repo_pkg.get_activities_for_member("m1", use_cache=False)
    repo_pkg.clear_activities_cache()
    assert repo_pkg.save_error_log("API通信エラー", "msg", "analysis") is True

    assert "get_all_members" in fake.calls
    assert ("create_member", {"名前": "X"}) in fake.calls
    assert ("m1", False) in fake.calls
    assert "clear" in fake.calls
    assert ("error", "API通信エラー", "未対応") in fake.calls


def test_notion_repository_implements_full_interface():
    # 抽象メソッドが未実装だとインスタンス化で TypeError になる。
    # 生成できる＝インターフェースを完全実装している。
    assert isinstance(NotionRepository(), DataRepository)

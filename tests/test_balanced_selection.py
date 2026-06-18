"""
バランスの取れたペア選定テストスイート
1人1件制限と同一スコア同等性の確認
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blendy.matching_engine import _select_balanced_pairs


class TestBalancedSelection:
    """1人1件制限と公平なペア選定をテスト"""

    def create_match(self, a_name, b_name, score):
        """テスト用マッチングレコードを生成"""
        return {
            "メンバーA名": a_name,
            "メンバーB名": b_name,
            "スコア": score,
            "協業タイプ": "A",
            "内訳": {},
            "マッチング理由": "test",
            "紹介文": "test",
        }

    def test_single_person_only_one_match(self):
        """同じ人が複数マッチングされない"""
        scored = [
            self.create_match("A", "B", 80),
            self.create_match("A", "C", 75),  # A は B とマッチング済みだから除外
            self.create_match("C", "D", 70),
        ]

        selected = _select_balanced_pairs(scored, max_count=3)

        # A が含まれるマッチングはせいぜい1件
        a_matches = [m for m in selected if m["メンバーA名"] == "A" or m["メンバーB名"] == "A"]
        assert len(a_matches) <= 1

    def test_max_count_respected(self):
        """max_count の上限が守られる"""
        scored = [
            self.create_match("A", "B", 80),
            self.create_match("C", "D", 75),
            self.create_match("E", "F", 70),
            self.create_match("G", "H", 65),
        ]

        selected = _select_balanced_pairs(scored, max_count=2)
        assert len(selected) <= 2

    def test_high_score_priority(self):
        """高スコアが優先される"""
        scored = [
            self.create_match("A", "B", 90),  # 高スコア
            self.create_match("C", "D", 50),  # 低スコア
        ]

        selected = _select_balanced_pairs(scored, max_count=1)

        # A-B ペアが選ばれるべき
        assert len(selected) == 1
        assert selected[0]["メンバーA名"] == "A"
        assert selected[0]["メンバーB名"] == "B"

    def test_empty_input(self):
        """空の入力でも動作する"""
        scored = []
        selected = _select_balanced_pairs(scored, max_count=10)
        assert selected == []

    def test_no_selection_when_limit_zero(self):
        """max_count=0 で選定されない"""
        scored = [
            self.create_match("A", "B", 80),
        ]

        selected = _select_balanced_pairs(scored, max_count=0)
        assert len(selected) == 0

    def test_name_count_tracking(self):
        """同じ人が複数回選ばれないこと"""
        scored = [
            self.create_match("A", "B", 80),
            self.create_match("A", "C", 79),
            self.create_match("A", "D", 78),
        ]

        selected = _select_balanced_pairs(scored, max_count=10)

        # A はせいぜい1回だけ選ばれる
        a_count = 0
        for match in selected:
            if match["メンバーA名"] == "A" or match["メンバーB名"] == "A":
                a_count += 1

        assert a_count <= 1

    def test_multiple_runs_consistency(self):
        """同じ入力で複数回実行しても同じ結果"""
        scored = [
            self.create_match("A", "B", 80),
            self.create_match("C", "D", 75),
            self.create_match("E", "F", 70),
        ]

        result1 = _select_balanced_pairs(scored, max_count=2)
        result2 = _select_balanced_pairs(scored, max_count=2)

        # 同じ順序で同じ結果が得られる
        assert len(result1) == len(result2)
        for m1, m2 in zip(result1, result2):
            assert m1["メンバーA名"] == m2["メンバーA名"]
            assert m1["メンバーB名"] == m2["メンバーB名"]

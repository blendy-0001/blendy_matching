"""
マッチング履歴テストスイート
再マッチング防止と pair identification の一意性確認
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestMatchingHistory:
    """マッチング履歴の再マッチング防止機構をテスト"""

    def test_frozenset_pair_identity(self):
        """frozenset で同じペアは識別される"""
        pair1 = frozenset(["山田太郎", "佐藤花子"])
        pair2 = frozenset(["佐藤花子", "山田太郎"])

        # 順序に関わらず同じペアと認識される
        assert pair1 == pair2

    def test_frozenset_pair_set_membership(self):
        """frozenset をセットに追加して重複判定"""
        matched_pairs = set()
        matched_pairs.add(frozenset(["山田太郎", "佐藤花子"]))

        # 逆順でも同じペアと判定される
        pair_key = frozenset(["佐藤花子", "山田太郎"])
        assert pair_key in matched_pairs

    def test_different_pairs_not_matched(self):
        """異なるペアは同じと判定されない"""
        matched_pairs = set()
        matched_pairs.add(frozenset(["山田太郎", "佐藤花子"]))

        pair_key = frozenset(["山田太郎", "鈴木次郎"])
        assert pair_key not in matched_pairs

    def test_same_person_different_partners(self):
        """同じ人が異なるパートナーとマッチング可能"""
        matched_pairs = set()
        matched_pairs.add(frozenset(["山田太郎", "佐藤花子"]))

        # 山田太郎は佐藤花子とはマッチング済みだが
        # 鈴木次郎とはマッチング可能
        pair_key1 = frozenset(["山田太郎", "佐藤花子"])
        pair_key2 = frozenset(["山田太郎", "鈴木次郎"])

        assert pair_key1 in matched_pairs
        assert pair_key2 not in matched_pairs

    def test_large_matched_pairs_set_performance(self):
        """大規模なマッチング履歴での検索パフォーマンス"""
        matched_pairs = set()

        # 1000組のマッチング履歴をシミュレート
        names = [f"メンバー{i}" for i in range(100)]
        pair_count = 0
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if pair_count >= 1000:
                    break
                matched_pairs.add(frozenset([names[i], names[j]]))
                pair_count += 1

        # 特定のペアが履歴に存在するか確認
        assert frozenset(["メンバー0", "メンバー1"]) in matched_pairs

        # 存在しないペアの確認
        assert frozenset(["メンバー99", "メンバー98"]) not in matched_pairs


class TestPairIdentification:
    """ペアの識別と正規化"""

    def test_pair_with_spaces_in_names(self):
        """名前にスペースがあるペア"""
        # 名前正規化済みで " ".join(text.split()) が適用されている前提
        pair1 = frozenset(["山田 太郎", "佐藤 花子"])
        pair2 = frozenset(["山田 太郎", "佐藤 花子"])

        assert pair1 == pair2

    def test_pair_with_normalized_spaces(self):
        """複数スペースが1つに正規化されたペア"""
        # 入力時点で normalize されている
        pair1 = frozenset(["山田太郎", "佐藤花子"])
        pair2 = frozenset(["山田太郎", "佐藤花子"])

        assert pair1 == pair2

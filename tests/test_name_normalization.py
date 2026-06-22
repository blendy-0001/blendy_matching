"""
名前正規化のテストスイート
スペース削除と内部スペース正規化の検証
"""
import pytest
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blendy.notion_client import _text


class TestNameNormalization:
    """_text() 関数の正規化動作をテスト"""

    def test_single_name_no_spaces(self):
        """スペースなしの名前"""
        props = {
            "名前": {"title": [{"plain_text": "山田太郎"}]}
        }
        result = _text(props, "名前")
        assert result == "山田太郎"

    def test_leading_trailing_spaces(self):
        """先頭と末尾のスペースを削除"""
        props = {
            "名前": {"title": [{"plain_text": "  山田太郎  "}]}
        }
        result = _text(props, "名前")
        assert result == "山田太郎"

    def test_internal_multiple_spaces_normalized(self):
        """内部の複数スペースを1つに正規化"""
        props = {
            "名前": {"title": [{"plain_text": "山田  太郎"}]}
        }
        result = _text(props, "名前")
        assert result == "山田 太郎"

    def test_multiple_internal_spaces(self):
        """複数の内部スペースを1つに正規化"""
        props = {
            "名前": {"title": [{"plain_text": "山田   太   郎"}]}
        }
        result = _text(props, "名前")
        assert result == "山田 太 郎"

    def test_tabs_and_newlines_normalized(self):
        """タブと改行も正規化"""
        props = {
            "名前": {"title": [{"plain_text": "山田\t太\n郎"}]}
        }
        result = _text(props, "名前")
        assert result == "山田 太 郎"

    def test_rich_text_multiple_items(self):
        """複数のリッチテキスト要素"""
        props = {
            "名前": {"rich_text": [
                {"plain_text": "山田"},
                {"plain_text": "  "},
                {"plain_text": "太郎"}
            ]}
        }
        result = _text(props, "名前")
        assert result == "山田 太郎"

    def test_empty_string(self):
        """空文字列"""
        props = {
            "名前": {"title": [{"plain_text": ""}]}
        }
        result = _text(props, "名前")
        assert result == ""

    def test_missing_property(self):
        """プロパティが存在しない場合"""
        props = {}
        result = _text(props, "名前")
        assert result == ""

    def test_none_text_field(self):
        """テキストフィールドがNone"""
        props = {
            "名前": {"title": None}
        }
        result = _text(props, "名前")
        assert result == ""

    def test_only_spaces(self):
        """スペースだけの場合"""
        props = {
            "名前": {"title": [{"plain_text": "   "}]}
        }
        result = _text(props, "名前")
        assert result == ""

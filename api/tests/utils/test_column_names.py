"""列名ユーティリティのテスト。"""

from economicon.utils.column_names import generate_unique_column_name


def test_generate_unique_column_name_returns_base_name() -> None:
    """未使用の基底名はそのまま返す。"""
    result = generate_unique_column_name("__tmp__", {"x", "y"})

    assert result == "__tmp__"


def test_generate_unique_column_name_appends_numeric_suffix() -> None:
    """衝突時は未使用になるまで数値サフィックスを進める。"""
    result = generate_unique_column_name(
        "__tmp__",
        {"__tmp__", "__tmp__1", "__tmp__2"},
    )

    assert result == "__tmp__3"

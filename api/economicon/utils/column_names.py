"""列名ユーティリティ。"""

from collections.abc import Collection


def generate_unique_column_name(
    base_name: str,
    used_names: Collection[str],
) -> str:
    """既存列名と衝突しない一意な列名を返す。"""
    candidate = base_name
    used_names_set = set(used_names)
    suffix = 1

    while candidate in used_names_set:
        candidate = f"{base_name}{suffix}"
        suffix += 1

    return candidate

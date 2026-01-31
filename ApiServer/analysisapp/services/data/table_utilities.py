from typing import Dict, List

import polars as pl


def rename_duplicate_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Polars DataFrame内の重複する列名に
    '_copy_1', '_copy_2' などのサフィックスを付けて
    リネームします。

    Args:
        df: リネーム対象のPolars DataFrame。

    Returns:
        列名が一意にリネームされた新しいPolars DataFrame。
    """
    # 現在の列名のリストを取得
    original_names: List[str] = df.columns

    # 新しい列名を格納するリスト
    new_names: List[str] = []

    # 各列名の出現回数を追跡する辞書
    counts: Dict[str, int] = {}

    for name in original_names:
        if name not in counts:
            # 初めて出現する列名
            new_names.append(name)
            counts[name] = 0
        else:
            # 2回目以降の出現（重複）
            counts[name] += 1
            new_name = f"{name}_copy_{counts[name]}"
            new_names.append(new_name)

    # 既存のDataFrameを新しい列名でリネーム
    # pl.DataFrame.rename() は辞書 {旧名: 新名} を期待するため、
    # zip()を使ってマッピングを作成し、元のDataFrameを複製してリネームします。
    rename_mapping = dict(zip(original_names, new_names))

    df_renamed = df.clone()
    df_renamed = df_renamed.rename(rename_mapping)

    return df_renamed

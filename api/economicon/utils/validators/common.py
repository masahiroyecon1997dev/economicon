from collections.abc import Mapping

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _

from ..exceptions import ValidationError


def validate_existence(
    *,
    value: str | list[str],
    valid_list: list[str],
    target: str,  # パラメータ名を渡す
) -> None:
    """
    指定された値がリスト内に存在することを検証する。
    テーブル名や列名が存在するかのチェックに使用する。
    Args:
        value: チェックする値（単体 or リスト）
        valid_list: 存在が確認されている値のリスト
        target: パラメータ名（'table_name', 'column_name' など）
    Raises:
        ValidationError: 値がリスト内に存在しない場合
    """
    targets = [value] if isinstance(value, str) else value
    valid_set = set(valid_list)

    # リスト内に存在しないものを抽出
    missing = [t for t in targets if t not in valid_set]

    if missing:
        # エラーコードは固定で「存在しない」ことを示すものに
        error_code = ErrorCode.DATA_NOT_FOUND

        # 多言語化メッセージ: 例 "columnName 'age' does not exist."
        missing_str = ", ".join(missing)
        message = _("{} '{}' does not exist.").format(target, missing_str)

        raise ValidationError(
            error_code=error_code, message=message, target=target
        )


def validate_non_existence(
    *, value: str | list[str], existing_list: list[str], target: str
) -> None:
    """
    指定された値が既にリスト内に存在しないことを検証する（重複チェック）。
    新しい列の作成や、新しいテーブルの作成時に使用する。

    Args:
        value: 新しく作ろうとしている名前（単体 or リスト）
        existing_list: 既に存在する名前のリスト
        target: パラメータ名（'new_column_name', 'table_name' など）

    Raises:
        ValidationError: 既に名前が存在する場合
    """
    targets = [value] if isinstance(value, str) else value
    existing_set = set(existing_list)

    # 既に存在するものを抽出
    already_exists = [t for t in targets if t in existing_set]

    if already_exists:
        # エラーコードは固定で「既に存在する」ことを示すものに
        error_code = ErrorCode.DATA_ALREADY_EXISTS

        # 多言語化メッセージ: 例 "tableName 'users' already exists."
        exists_str = ", ".join(already_exists)
        message = _("{} '{}' already exists.").format(target, exists_str)

        raise ValidationError(
            error_code=error_code, message=message, target=target
        )


def validate_numeric_types(
    *,
    schema: Mapping[str, pl.DataType],
    columns: str | list[str],
    target: str = "columns",
) -> None:
    """指定された列が数値型であることを検証する。

    Args:
        schema: 列名とデータ型のマッピング
        columns: 検証対象の列名（単体 or リスト）
        target: パラメータ名（デフォルトは "columns"）

    Raises:
        ValidationError: 数値型でない列が存在する場合
    """
    targets = [columns] if isinstance(columns, str) else columns

    invalid_types = []
    for col in targets:
        dtype = schema[col]

        # .is_numeric() メソッドで判定
        # 整数(Int), 浮動小数点(Float), 符号なし整数(UInt) すべて判定可能
        if not dtype.is_numeric():
            invalid_types.append(f"{col}({dtype})")

    if invalid_types:
        raise ValidationError(
            error_code=ErrorCode.INVALID_DTYPE,
            message=_("The following columns must be numeric: {}").format(
                ", ".join(invalid_types)
            ),
            target=target,
        )


def validate_row_count_limit(
    *,
    current_row_count: int,  # dfそのものではなく数値を受け取る
    requested_count: int,
    target: str = "row_count",
) -> None:
    """
    指定された行数がテーブルの総行数を超えていないか検証する。

    Args:
        current_row_count: テーブルの総行数
        requested_count: クライアントが要求している行数
        target: パラメータ名（デフォルトは "row_count"）

    Raises:
        ValidationError: 要求された行数が総行数を超えている場合
    """
    if requested_count > current_row_count:
        raise ValidationError(
            error_code=ErrorCode.ROW_OUT_OF_RANGE,
            message=_(
                "Requested {} ({}) exceeds the available rows ({})."
            ).format(target, requested_count, current_row_count),
            target=target,
        )

import os
from pathlib import Path
from typing import Any, List, Optional, Union

from economicon.i18n.translation import gettext as _


class ValidationError(Exception):
    """
    入力バリデーション専用の例外(全体で統一)
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_required(value: Union[str, int, float], param_name: str) -> None:
    """パラメータが空かどうかをチェック"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        message = _("{} is required.").format(param_name)
        raise ValidationError(message)
    return None


def validate_boolean(value: str, param_name: str) -> None:
    """パラメータが真偽値どうかをチェック"""
    if value not in ["true", "false"]:
        message = _("{} must be 'true' or 'false'.").format(param_name)
        raise ValidationError(message)
    return None


def validate_number(value: Union[str, int, float], param_name: str) -> None:
    """パラメータが数値どうかをチェック"""
    try:
        float(value)
        return None
    except (ValueError, TypeError):
        message = _("{} must be a number.").format(param_name)
        raise ValidationError(message)


def validate_integer(value: Union[str, int, float], param_name: str) -> None:
    """パラメータが整数どうかをチェック"""
    try:
        int(value)
        return None
    except (ValueError, TypeError):
        message = _("{} must be an integer.").format(param_name)
        raise ValidationError(message)


def validate_integer_positive(
    value: Union[str, int, float], param_name: str
) -> None:
    """パラメータが正の整数どうかをチェック"""
    try:
        int_value = int(value)
        if int_value <= 0:
            message = _("{} must be a positive integer.").format(param_name)
            raise ValidationError(message)
        return None
    except (ValueError, TypeError):
        message = _("{} must be a positive integer.").format(param_name)
        raise ValidationError(message)


def validate_string(value: str, param_name: str) -> None:
    """パラメータが文字列どうかをチェック"""
    if not isinstance(value, str) or not value.strip():
        message = _("{} must be a string.").format(param_name)
        raise ValidationError(message)
    return None


def validate_required_list(value: List, param_name: str) -> None:
    """パラメータがリストどうかをチェック"""
    if not isinstance(value, list):
        message = _("{} must be a list.").format(param_name)
        raise ValidationError(message)
    return None


def validate_list_length(
    value: List, required_num_list: int, param_name: str, item_name: str
) -> None:
    """リストの長さをチェック"""
    if len(value) < required_num_list:
        message = _("{} must be with at least {} {}.").format(
            param_name, required_num_list, item_name
        )
        raise ValidationError(message)
    return None


def validate_item_in_dict(
    value: dict,
    dictionary_name: str,
    param_name: str,
) -> None:
    """辞書のキーにその値があるかのバリデーション"""
    if dictionary_name not in value:
        message = _("{} '{}' does not exist.").format(
            param_name, dictionary_name
        )
        raise ValidationError(message)
    return None


def validate_string_length(
    value: str,
    param_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> None:
    """文字列の長さをチェック"""
    if min_length is not None and len(value) < min_length:
        message = _("{} must be at least {} characters long.").format(
            param_name, min_length
        )
        raise ValidationError(message)
    if max_length is not None and len(value) > max_length:
        message = _("{} must be at most {} characters long.").format(
            param_name, max_length
        )
        raise ValidationError(message)
    return None


def validate_invalid_chars(
    value: str, param_name: str, invalid_chars: List[str]
) -> None:
    """無効な文字が含まれているかチェック"""
    message = _("{} contains invalid characters.").format(param_name)
    for char in invalid_chars:
        if char in value:
            raise ValidationError(message)
    return None


def validate_numeric_range(
    value: Union[int, float],
    param_name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
) -> None:
    """数値の範囲をチェック"""
    if min_value is not None and value < min_value:
        message = _("{} must be between {} and {}.").format(
            param_name, min_value, max_value
        )
        raise ValidationError(message)
    if max_value is not None and value > max_value:
        message = _("{} must be between {} and {}.").format(
            param_name, min_value, max_value
        )
        raise ValidationError(message)
    return None


def validate_enum(
    value: str, param_name: str, allowed_values: List[str]
) -> None:
    """列挙型の値をチェック"""
    if value not in allowed_values:
        message = _("{} is invalid value.").format(param_name)
        raise ValidationError(message)
    return None


def validate_path(value: str, param_name: str) -> None:
    """パスのバリデーション"""
    # 空のパスをチェック
    message = _("{} is required.").format(param_name)
    validate_required(value, param_name)
    # 危険な文字列をチェック
    dangerous_patterns = ["..", "~", "$", "|", ";", "&", "`"]
    if any(pattern in value for pattern in dangerous_patterns):
        raise ValidationError(message)
    # 絶対パスかどうかをチェック
    try:
        Path(value).resolve()
    except (OSError, ValueError):
        raise ValidationError(message)
    return None


def validate_item_exists_in_list(
    value: str, param_name: str, item_name_list: List[str]
) -> None:
    """項目が存在するかチェック"""
    if value not in item_name_list:
        message = _("{} '{}' does not exist.").format(param_name, value)
        raise ValidationError(message)
    return None


def validate_item_duplicate(
    value: str, param_name: str, item_name_list: List[str]
) -> None:
    """項目が重複していないかチェック"""
    if value in item_name_list:
        message = _("{} '{}' already exists.").format(param_name, value)
        raise ValidationError(message)
    return None


def validate_candidates(
    value: str, param_name: str, candidate_values: List[str]
) -> None:
    """リスト内にその値があるかのバリデーション"""
    if value not in candidate_values:
        message = _("{} '{}' is not supported. Supported {}: {}").format(
            param_name, value, param_name, ", ".join(candidate_values)
        )
        raise ValidationError(message)
    return None


def validate_file_path_exists(file_path: str, param_name: str) -> None:
    """ファイルパスのバリデーション"""
    if not os.path.exists(file_path):
        message = _("{} does not exist: {}").format(param_name, file_path)
        raise ValidationError(message)
    return None


def validate_directory_path_exists(directory: str, param_name: str) -> None:
    """ディレクトリパスのバリデーション"""
    if not os.path.exists(directory):
        raise ValidationError(
            _("ディレクトリが存在しません: {}").format(directory)
        )
    return None


def validate_file_path_readable(file_path: str, param_name: str) -> None:
    """ファイルパスのバリデーション"""
    if not os.access(file_path, os.R_OK):
        message = _("{} is not readable: {}").format(param_name, file_path)
        raise ValidationError(message)
    return None


def validate_column_is_numeric(
    column_name: str, param_name: str, column_type: Any
) -> None:
    """列が数値型であるかチェック"""
    if not column_type.is_numeric():
        message = _("{} '{}' is not numeric.").format(param_name, column_name)
        raise ValidationError(message)
    return None

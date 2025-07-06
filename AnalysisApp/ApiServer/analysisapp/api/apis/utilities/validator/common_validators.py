from pathlib import Path
from typing import Optional, List, Union, Dict
from django.utils.translation import gettext as _
from rest_framework import status
from ....apis.data.tables_info import TableInfo


class CommonValidationError(Exception):
    """
    入力バリデーション専用の例外
    """
    def __init__(self,
                 message: str,
                 status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def validate_required(value: Union[str, int, float], param_name: str) -> None:
    """パラメータが空かどうかをチェック"""
    if value is None or not value:
        message = _(f"{param_name} is required.")
        raise CommonValidationError(message)
    return None


def validate_boolean(value: str, param_name: str) -> None:
    """パラメータが真偽値どうかをチェック"""
    if value not in ['true', 'false']:
        message = _(f"{param_name} must be 'true' or 'false'.")
        raise CommonValidationError(message)
    return None


def validate_number(value: Union[int, float], param_name: str) -> None:
    """パラメータが数値どうかをチェック"""
    if (not isinstance(value, (int, float))):
        message = _(f"{param_name} must be a number.")
        raise CommonValidationError(message)
    return None


def validate_string(value: str, param_name: str) -> None:
    """パラメータが文字列どうかをチェック"""
    if (isinstance(value, str) and not value.strip()):
        message = _(f"{param_name} mustbe a string.")
        raise CommonValidationError(message)
    return None


def validate_required_list(value: List, param_name: str) -> None:
    """パラメータがリストどうかをチェック"""
    if not isinstance(value, list):
        message = _(f"{param_name} must be a list.")
        raise CommonValidationError(message)
    return None


def validate_list_length(value: List, param_name: str) -> None:
    """リストの長さをチェック"""
    if len(value) < 1:
        message = _(f"{param_name} must be a list with at least one item.")
        raise CommonValidationError(message)
    return None


def validate_string_length(value: str,
                           param_name: str,
                           min_length: Optional[int] = None,
                           max_length: Optional[int] = None) -> None:
    """文字列の長さをチェック"""
    if min_length is not None and len(value) < min_length:
        message = _(f"{param_name} must be at {min_length} to {max_length} "
                    f"characters long.")
        raise CommonValidationError(message)
    if max_length is not None and len(value) > max_length:
        message = _(f"{param_name} must be at {min_length} to {max_length} "
                    f"characters long.")
        raise CommonValidationError(message)
    return None


def validate_invalid_chars(value: str, param_name: str,
                           invalid_chars: List[str]) -> None:
    """無効な文字が含まれているかチェック"""
    message = _(f"{param_name} contains invalid characters.")
    for char in invalid_chars:
        if char in value:
            raise CommonValidationError(message)
    return None


def validate_numeric_range(value: Union[int, float], param_name: str,
                           min_value: Optional[Union[int, float]] = None,
                           max_value: Optional[Union[int, float]] = None
                           ) -> None:
    """数値の範囲をチェック"""
    if min_value is not None and value < min_value:
        message = _(f"{param_name} must be between {min_value} "
                    f"and {max_value}.")
        raise CommonValidationError(message)
    if max_value is not None and value > max_value:
        message = _(f"{param_name} must be between {min_value} "
                    f"and {max_value}.")
        raise CommonValidationError(message)
    return None


def validate_enum(value: str, param_name: str,
                  allowed_values: List[str]) -> None:
    """列挙型の値をチェック"""
    if value not in allowed_values:
        message = _(f"{param_name} is invalid value.")
        raise CommonValidationError(message)
    return None


def validate_path(value: str, param_name: str) -> None:
    """パスのバリデーション"""
    # 空のパスをチェック
    message = _(f"{param_name} is required.")
    if validate_required(value, param_name):
        raise CommonValidationError(message)
    # 危険な文字列をチェック
    dangerous_patterns = ['..', '~', '$', '|', ';', '&', '`']
    if any(pattern in value for pattern in dangerous_patterns):
        raise CommonValidationError(message)
    # 絶対パスかどうかをチェック
    try:
        Path(value).resolve()
    except (OSError, ValueError):
        raise CommonValidationError(message)
    return None


def validate_table_exists(value: str,
                          param_name: str,
                          tables: Dict[str, TableInfo]) -> None:
    """テーブルが存在するかチェック"""
    if value not in tables:
        message = _(f"{param_name} '{value}' does not exist.")
        raise CommonValidationError(message)
    return None


def validate_table_duplicate(value: str,
                             param_name: str,
                             tables: Dict[str, TableInfo]) -> None:
    """テーブルが重複していないかチェック"""
    if value in tables:
        message = _(f"{param_name} '{value}' already exists.")
        raise CommonValidationError(message)
    return None


def validate_column_exists(value: str,
                           param_name: str,
                           columns: List[str]) -> None:
    """列が存在するかチェック"""
    if value not in columns:
        message = _(f"{param_name} '{value}' does not exist.")
        raise CommonValidationError(message)
    return None


def validate_column_duplicate(value: str,
                              param_name: str,
                              columns: List[str]) -> None:
    """列が重複していないかチェック"""
    message = _(f"{param_name} '{value}' already exists.")
    if value in columns:
        raise CommonValidationError(message)
    return None


def validate_condition(value: str,
                       param_name: str,
                       condition_candidates: List[str]) -> None:
    """フィルタ条件のバリデーション"""
    if value not in condition_candidates:
        message = _(f"{param_name} '{value}' is not a valid condition.")
        raise CommonValidationError(message)
    return None

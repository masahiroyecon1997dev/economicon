from pathlib import Path
from typing import Optional, List, Union
from rest_framework import status
from django.utils.translation import gettext as _
from ..create_response import create_error_response


def validate_required(value: any, param_name: str) -> None:
    """パラメータが空かどうかをチェック"""
    if value is None or not value:
        messege = _(f"{param_name} is required.")
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                messege
            )
    return None


def validate_number(value: any, param_name: str) -> None:
    """パラメータが数値どうかをチェック"""
    if (not isinstance(value, (int, float))):
        messege = _(f"{param_name} must be a number.")
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                messege
            )
    return None


def validate_required_string(value: any, param_name: str) -> None:
    """パラメータが文字列どうかをチェック"""
    if (isinstance(value, str) and not value.strip()):
        messege = _(f"{param_name} mustbe a string.")
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                messege
            )
    return None


def validate_string_length(value: any,
                           param_name: str,
                           min_length: Optional[int] = None,
                           max_length: Optional[int] = None) -> None:
    """文字列の長さをチェック"""
    if min_length is not None and len(value) < min_length:
        message = _(f"{param_name} must be at {min_length} to {max_length} "
                    f"characters long.")
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message
            )
    if max_length is not None and len(value) > max_length:
        message = _(f"{param_name} must be at {min_length} to {max_length} "
                    f"characters long.")
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message
            )
    return None


def validate_invalid_chars(value: str, param_name: str,
                           invalid_chars: List[str]) -> None:
    """無効な文字が含まれているかチェック"""
    message = _(f"{param_name} contains invalid characters.")
    for char in invalid_chars:
        if char in value:
            raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message
            )
    return None


def validate_numeric_range(value: Union[int, float], param_name: str,
                           min_value: Optional[Union[int, float]] = None,
                           max_value: Optional[Union[int, float]] = None
                           ) -> None:
    """数値の範囲をチェック"""
    if min_value is not None and value < min_value:
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                f"{param_name} must be between {min_value} and {max_value}."
            )
    if max_value is not None and value > max_value:
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                f"{param_name} must be between {min_value} and {max_value}."
            )
    return None


def validate_enum(value: any, param_name: str,
                  allowed_values: List[any]) -> None:
    """列挙型の値をチェック"""
    if value not in allowed_values:
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                f"{param_name} is invalid value."
            )
    return None


def validate_path(value: str, param_name: str) -> None:
    """パスのバリデーション"""
    # 空のパスをチェック
    if validate_required(value, param_name):
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                f"{param_name} is required."
            )
    # 危険な文字列をチェック
    dangerous_patterns = ['..', '~', '$', '|', ';', '&', '`']
    if any(pattern in value for pattern in dangerous_patterns):
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                f"{param_name} is required."
            )
    # 絶対パスかどうかをチェック
    try:
        Path(value).resolve()
    except (OSError, ValueError):
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                f"{param_name} is required."
            )
    return None


def validate_table_exists(value: str, tables: dict) -> None:
    """テーブルが存在するかチェック"""
    if value not in tables:
        raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                f"The table '{value}' does not exist."
            )
    return None

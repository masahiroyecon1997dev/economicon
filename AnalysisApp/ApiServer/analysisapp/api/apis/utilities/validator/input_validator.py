from typing import List, Optional, Union
from rest_framework import status
from ...data.tables import tables
from .common_validators import (validate_required, validate_string_length,
                                validate_invalid_chars, validate_table_exists)


class InputValidationError(Exception):
    """
    入力バリデーション専用の例外
    """
    def __init__(self,
                 message: str,
                 status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InputValidator:

    def __init__(self,
                 invalid_chars: List[str] = None,
                 table_name_min_length: Optional[int] = None,
                 table_name_max_length: Optional[int] = None,
                 column_name_min_length: Optional[int] = None,
                 column_name_max_length: Optional[int] = None):
        self.invalid_chars = invalid_chars
        self.table_name_min_length = table_name_min_length
        self.table_name_max_length = table_name_max_length
        self.column_name_min_length = column_name_min_length
        self.column_name_max_length = column_name_max_length

    def validate_new_table_name(self, value: str) -> None:
        """テーブル名のバリデーション"""
        param_name = 'tableName'
        validate_required(value, param_name)
        validate_string_length(value,
                               param_name,
                               self.table_name_min_length,
                               self.table_name_max_length)

    def validate_column_name(self, value: str, param_name: str) -> None:
        """カラム名のバリデーション"""
        validate_required(value, param_name)
        validate_string_length(value,
                               param_name,
                               self.table_name_min_length,
                               self.table_name_max_length)

from typing import List, Optional, Dict
from rest_framework import status
from ....apis.data.tables_info import TableInfo
from .common_validators import (CommonValidationError,
                                validate_required,
                                validate_number,
                                validate_string_length,
                                validate_invalid_chars,
                                validate_table_duplicate,
                                validate_table_exists,
                                validate_column_duplicate,
                                validate_column_exists)


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

    PARAM_TABLE_NAME = 'tableName'
    PARAM_TABLE_NUM_ROWS = 'tableNumberOfRows'
    PARAM_COLUMN_NAMES = 'columnName'
    PARAM_NEWCOLUMN_NAME = 'newColumnName'

    def __init__(self,
                 invalid_chars: List[str] = [],
                 table_name_min_length: Optional[int] = None,
                 table_name_max_length: Optional[int] = None,
                 column_name_min_length: Optional[int] = None,
                 column_name_max_length: Optional[int] = None):
        self.invalid_chars = invalid_chars
        self.table_name_min_length = table_name_min_length
        self.table_name_max_length = table_name_max_length
        self.column_name_min_length = column_name_min_length
        self.column_name_max_length = column_name_max_length

    def validate_new_table_name(self,
                                table_name: str,
                                tables_info: Dict[str, TableInfo]
                                ) -> None:
        # 新規テーブル名のバリデーション
        try:
            validate_required(table_name, self.PARAM_TABLE_NAME)
            validate_string_length(table_name,
                                   self.PARAM_TABLE_NAME,
                                   self.table_name_min_length,
                                   self.table_name_max_length)
            validate_invalid_chars(table_name, self.PARAM_TABLE_NAME,
                                   self.invalid_chars)
            validate_table_duplicate(table_name,
                                     self.PARAM_TABLE_NAME,
                                     tables_info)
            return None
        except CommonValidationError as e:
            raise InputValidationError(
                message=e.message,
                status_code=e.status_code
            )

    def validate_table_num_rows(self,
                                table_num_rows: int
                                ) -> None:
        # テーブルの行数のバリデーション
        try:
            validate_required(table_num_rows, self.PARAM_TABLE_NUM_ROWS)
            validate_number(table_num_rows, self.PARAM_TABLE_NUM_ROWS)
            return None
        except CommonValidationError as e:
            raise InputValidationError(
                message=e.message,
                status_code=e.status_code
            )

    def validate_new_column_name(self,
                                 new_column_name: str,
                                 columns: List[str]
                                 ) -> None:
        # 新しいカラム名のバリデーション
        try:
            validate_required(new_column_name, self.PARAM_NEWCOLUMN_NAME)
            validate_string_length(new_column_name,
                                   self.PARAM_COLUMN_NAMES,
                                   self.column_name_min_length,
                                   self.column_name_max_length)
            validate_invalid_chars(new_column_name, self.PARAM_COLUMN_NAMES,
                                   self.invalid_chars)
            validate_column_duplicate(new_column_name,
                                      self.PARAM_NEWCOLUMN_NAME,
                                      columns)
            return None
        except CommonValidationError as e:
            raise InputValidationError(
                message=e.message,
                status_code=e.status_code
            )

    def validate_existed_table_name(self,
                                    table_name: str,
                                    tables_info: Dict[str, TableInfo]
                                    ) -> None:
        # 既存のテーブル名のバリデーション
        try:
            validate_required(table_name, self.PARAM_TABLE_NAME)
            validate_table_exists(table_name,
                                  self.PARAM_TABLE_NAME,
                                  tables_info)
            return None
        except CommonValidationError as e:
            raise InputValidationError(
                message=e.message,
                status_code=e.status_code
            )

    def validate_existed_column_name(self,
                                     column_name: str,
                                     table_info: TableInfo
                                     ) -> None:
        # 既存のカラム名のバリデーション
        param_insert_position_column = 'insertPositionColumn'
        try:
            validate_required(column_name, self.PARAM_COLUMN_NAMES)
            validate_column_exists(column_name,
                                   param_insert_position_column,
                                   table_info.table.columns)
            return None
        except CommonValidationError as e:
            raise InputValidationError(
                message=e.message,
                status_code=e.status_code
            )

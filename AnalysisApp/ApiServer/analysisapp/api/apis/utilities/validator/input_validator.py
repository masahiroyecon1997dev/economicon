
from typing import List, Optional
from .validator_utils import remove_one_string_copy
from .common_validators import (
    validate_required,
    validate_boolean,
    validate_number,
    validate_required_list,
    validate_list_length,
    validate_string_length,
    validate_invalid_chars,
    validate_table_duplicate,
    validate_table_exists,
    validate_column_duplicate,
    validate_column_exists,
    validate_numeric_range,
    validate_candidates
)


class InputValidator:
    def __init__(
        self,
        param_names: Optional[dict] = None,
        invalid_chars: Optional[List[str]] = None,
        table_name_min_length: Optional[int] = None,
        table_name_max_length: Optional[int] = None,
        column_name_min_length: Optional[int] = None,
        column_name_max_length: Optional[int] = None,
        condition_candidates: Optional[List[str]] = None
    ):
        self.param_names = param_names or {
            'table_name': 'tableName',
            'column_names': 'columnName'
        }
        self.invalid_chars = invalid_chars if invalid_chars is not None else []
        self.table_name_min_length = table_name_min_length
        self.table_name_max_length = table_name_max_length
        self.column_name_min_length = column_name_min_length
        self.column_name_max_length = column_name_max_length
        self.condition_candidates = condition_candidates or []

    def validate_new_table_name(
        self, table_name: str, table_name_list: List[str]
    ) -> None:
        # 新規テーブル名のバリデーション
        param = self.param_names['table_name']
        validate_required(table_name, param)
        validate_string_length(
            table_name, param,
            self.table_name_min_length, self.table_name_max_length
        )
        validate_invalid_chars(table_name, param, self.invalid_chars)
        validate_table_duplicate(table_name, param, table_name_list)
        return None

    def validate_table_num_rows(self, table_num_rows: int) -> None:
        param = self.param_names['table_num_rows']
        validate_required(table_num_rows, param)
        validate_number(table_num_rows, param)
        return None

    def validate_new_columns(self, columns: List[str]) -> None:
        param = self.param_names['column_names']
        validate_required_list(columns, param)
        validate_list_length(columns, param)
        for column in columns:
            columns_removed_target_column = remove_one_string_copy(
                columns, column
            )
            validate_required(column, param)
            validate_string_length(
                column, param,
                self.column_name_min_length, self.column_name_max_length
            )
            validate_invalid_chars(column, param, self.invalid_chars)
            validate_column_duplicate(
                column, param, columns_removed_target_column
            )
        return None

    def validate_new_column_name(
        self, new_column_name: str, columns: List[str]
    ) -> None:
        param = self.param_names['new_column_name']
        validate_required(new_column_name, param)
        validate_string_length(
            new_column_name, param,
            self.column_name_min_length, self.column_name_max_length
        )
        validate_invalid_chars(new_column_name, param, self.invalid_chars)
        validate_column_duplicate(new_column_name, param, columns)
        return None

    def validate_existed_table_name(
        self, table_name: str, table_name_list: List[str]
    ) -> None:
        param = self.param_names['table_name']
        validate_required(table_name, param)
        validate_table_exists(table_name, param, table_name_list)
        return None

    def validate_existed_column_name(
        self, column_name: str, column_name_list: List[str]
    ) -> None:
        param = self.param_names['column_names']
        validate_required(column_name, param)
        validate_column_exists(
            column_name, param, column_name_list
        )
        return None

    def validate_row_index(self, value: int, max_row_number: int) -> None:
        param = self.param_names['row_index']
        validate_required(value, param)
        validate_number(value, param)
        validate_numeric_range(
            value, param, min_value=0, max_value=max_row_number - 1
        )
        return None

    def validate_filter_condition(self, value: str) -> None:
        param = self.param_names['condition']
        validate_required(value, param)
        validate_candidates(value, param, self.condition_candidates)
        return None

    def validate_is_compare_column(self, is_compare_column: str) -> None:
        param = self.param_names['is_compare_column']
        validate_required(is_compare_column, param)
        validate_boolean(is_compare_column, param)
        return None

    def validate_compare_value(self, compare_value: str) -> None:
        param = self.param_names['compare_value']
        validate_required(compare_value, param)
        return None

    def validate_join_type(self, join_type: str) -> None:
        param = self.param_names['join_type']
        join_type_candidates = ['inner', 'left', 'right', 'outer']
        validate_candidates(join_type, param, join_type_candidates)
        return None

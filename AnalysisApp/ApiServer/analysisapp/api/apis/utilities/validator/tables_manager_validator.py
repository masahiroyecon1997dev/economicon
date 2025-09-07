from typing import List, Optional
import polars as pl
from .validator_utils import remove_one_string_copy
from .common_validators import (
    validate_required,
    validate_boolean,
    validate_number,
    validate_integer,
    validate_required_list,
    validate_list_length,
    validate_string_length,
    validate_invalid_chars,
    validate_item_exists_in_list,
    validate_item_duplicate,
    validate_numeric_range,
    validate_candidates,
    validate_file_path_exists,
    validate_directory_path_exists,
    validate_column_is_numeric
)
from .validation_config import (TABLES_MANAGER_VALIDATOR_CONFIG,
                                FILTER_CONDITION_CANDIDATES)


def validate_file_path(
    file_path: str,
    file_path_param: str
) -> None:
    validate_required(file_path, file_path_param)
    validate_file_path_exists(file_path, file_path_param)


def validate_directory_path(
    directory: str,
    directory_param: str
) -> None:
    validate_required(directory, directory_param)
    validate_directory_path_exists(directory, directory_param)


def validate_file_name(
    file_name: str,
    file_name_param: str,
    invalid_chars: Optional[List[str]] = None
) -> None:
    if invalid_chars is None:
        invalid_chars = []
    validate_required(file_name, file_name_param)
    validate_string_length(
        file_name,
        file_name_param,
        min_length=1,
        max_length=255,
    )
    validate_invalid_chars(file_name, file_name_param, invalid_chars)


def validate_separator(
    separator: str,
    separator_param: str
) -> None:
    validate_string_length(
        separator,
        separator_param,
        min_length=1,
        max_length=5,
    )


def validate_sheet_name(
    sheet_name: Optional[str],
    sheet_name_param: str
) -> None:
    if sheet_name is not None:
        validate_string_length(
            sheet_name,
            sheet_name_param,
            min_length=1,
            max_length=255,
        )


def validate_new_table_name(
    table_name: str,
    table_name_list: List[str],
    table_name_param: str,
    invalid_chars: Optional[List[str]] = None
) -> None:
    if invalid_chars is None:
        invalid_chars = []
    table_name_min_length = TABLES_MANAGER_VALIDATOR_CONFIG.get(
        "table_name_min_length", 1)
    table_name_max_length = TABLES_MANAGER_VALIDATOR_CONFIG.get(
        "table_name_max_length", 255)
    validate_required(table_name, table_name_param)
    validate_string_length(
        table_name,
        table_name_param,
        table_name_min_length,
        table_name_max_length,
    )
    validate_invalid_chars(table_name, table_name_param, invalid_chars)
    validate_item_duplicate(table_name, table_name_param, table_name_list)


def validate_table_num_rows(
    table_num_rows: int,
    table_num_rows_param: str
) -> None:
    validate_required(table_num_rows, table_num_rows_param)
    validate_number(table_num_rows, table_num_rows_param)


def validate_new_columns(
    columns: List[str],
    column_names_param: str,
    invalid_chars: Optional[List[str]] = None
) -> None:
    if invalid_chars is None:
        invalid_chars = []
    least_num_columns = 1
    validate_required_list(columns, column_names_param)
    validate_list_length(columns, least_num_columns,
                         column_names_param, 'item')
    column_name_min_length = TABLES_MANAGER_VALIDATOR_CONFIG.get(
        "column_name_min_length", 1)
    column_name_max_length = TABLES_MANAGER_VALIDATOR_CONFIG.get(
        "column_name_max_length", 255)
    for column in columns:
        columns_removed_target_column = remove_one_string_copy(columns, column)
        validate_required(column, column_names_param)
        validate_string_length(
            column,
            column_names_param,
            column_name_min_length,
            column_name_max_length,
        )
        validate_invalid_chars(column, column_names_param, invalid_chars)
        validate_item_duplicate(column, column_names_param,
                                columns_removed_target_column)


def validate_new_column_name(
    new_column_name: str,
    columns: List[str],
    new_column_name_param: str,
    invalid_chars: Optional[List[str]] = None
) -> None:
    if invalid_chars is None:
        invalid_chars = []
    column_name_min_length = TABLES_MANAGER_VALIDATOR_CONFIG.get(
        "column_name_min_length", 1)
    column_name_max_length = TABLES_MANAGER_VALIDATOR_CONFIG.get(
        "column_name_max_length", 255)
    validate_required(new_column_name, new_column_name_param)
    validate_string_length(
        new_column_name,
        new_column_name_param,
        column_name_min_length,
        column_name_max_length,
    )
    validate_invalid_chars(new_column_name,
                           new_column_name_param,
                           invalid_chars)
    validate_item_duplicate(new_column_name, new_column_name_param, columns)


def validate_existed_table_name(
    table_name: str,
    table_name_list: List[str],
    table_name_param: str
) -> None:
    validate_required(table_name, table_name_param)
    validate_item_exists_in_list(table_name,
                                 table_name_param,
                                 table_name_list)


def validate_existed_tables(
    table_names: List[str],
    table_name_list: List[str],
    table_names_param: str
) -> None:
    validate_required_list(table_names, table_names_param)
    least_num_tables = 2
    validate_list_length(table_names, least_num_tables,
                         table_names_param, 'tableName')
    for table_name in table_names:
        validate_existed_table_name(table_name,
                                    table_name_list,
                                    table_names_param)


def validate_existed_column_name(
    column_name: str,
    column_name_list: List[str],
    column_names_param: str
) -> None:
    validate_required(column_name, column_names_param)
    validate_item_exists_in_list(column_name,
                                 column_names_param,
                                 column_name_list)


def validate_existed_columns(
    column_names: List[str],
    column_name_list: List[str],
    column_names_param: str
) -> None:
    validate_required_list(column_names, column_names_param)
    least_num_columns = 1
    validate_list_length(column_names, least_num_columns,
                         column_names_param, 'columnName')
    for column_name in column_names:
        validate_existed_column_name(column_name,
                                     column_name_list,
                                     column_names_param)


def validate_row_index(
    value: int,
    max_row_number: int,
    row_index_param: str
) -> None:
    validate_required(value, row_index_param)
    validate_integer(value, row_index_param)
    int_value = int(value)
    validate_numeric_range(
        int_value,
        row_index_param,
        min_value=1,
        max_value=max_row_number,
    )


def validate_filter_condition(
    value: str,
    condition_param: str,
    condition_candidates: Optional[List[str]] = None
) -> None:
    if condition_candidates is None:
        condition_candidates = FILTER_CONDITION_CANDIDATES
    validate_required(value, condition_param)
    validate_candidates(value, condition_param, condition_candidates)


def validate_is_compare_column(
    is_compare_column: str,
    is_compare_column_param: str
) -> None:
    validate_required(is_compare_column, is_compare_column_param)
    validate_boolean(is_compare_column, is_compare_column_param)


def validate_compare_value(
    compare_value: str,
    compare_value_param: str
) -> None:
    validate_required(compare_value, compare_value_param)


def validate_join_type(
    join_type: str,
    join_type_param: str
) -> None:
    join_type_candidates = ['inner', 'left', 'right', 'outer']
    validate_candidates(join_type, join_type_param, join_type_candidates)


def validate_calculation_expression(
    expression: str,
    calculation_expression_param: str
) -> None:
    validate_required(expression, calculation_expression_param)


def validate_existed_numeric_columns(
    column_names: List[str],
    column_name_list: List[str],
    df_schema: pl.Schema,
    calculation_expression_param: str,
    column_names_param: str
) -> None:
    least_num_columns = 1
    validate_list_length(column_names, least_num_columns,
                         calculation_expression_param, 'column')
    for col_name in column_names:
        validate_required(col_name, column_names_param)
        validate_item_exists_in_list(col_name,
                                     column_names_param,
                                     column_name_list)
        column_type = df_schema.items().mapping[col_name]
        validate_column_is_numeric(col_name, column_names_param, column_type)

from typing import List
from rest_framework.response import Response
from .input_validator import (InputValidationError, InputValidator)
from .input_validation_config import (INPUT_VALIDATOR_CONFIG)
from typing import Optional
from ....apis.data.tables_info import all_tables_info
from ..create_response import create_error_response


def validate_create_table_request(request_data) -> Optional[Response]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)

        table_name = request_data['tableName']
        validator.validate_new_table_name(table_name, all_tables_info)

        table_number_of_rows = request_data['tableNumberOfRows']
        validator.validate_table_num_rows(table_number_of_rows)

        columns: List[str] = request_data['columns']
        validator.validate_new_columns(columns)

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )


def validate_rename_table_request(request_data) -> Optional[Response]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)

        old_table_name = request_data['oldTableName']
        validator.validate_existed_table_name(old_table_name, all_tables_info)

        new_table_name = request_data['newTableName']
        validator.validate_new_table_name(new_table_name, all_tables_info)

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )


def validate_delete_table_request(request_data) -> Optional[Response]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)

        table_name = request_data['tableName']
        validator.validate_existed_table_name(table_name, all_tables_info)

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )


def validate_add_column_request(request_data) -> Optional[Response]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)

        table_name = request_data['tableName']
        validator.validate_existed_table_name(table_name, all_tables_info)

        new_column_name = request_data['newColumnName']
        table_info = all_tables_info[table_name]
        validator.validate_new_column_name(new_column_name,
                                           table_info.table.columns)

        insert_position_column = request_data['addPositionColumn']
        validator.validate_existed_column_name(insert_position_column,
                                               table_info)

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )


def validate_rename_column_request(request_data) -> Optional[Response]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)

        table_name = request_data['tableName']
        validator.validate_existed_table_name(table_name, all_tables_info)

        old_column_name = request_data['oldColumnName']
        table_info = all_tables_info[table_name]
        validator.validate_existed_column_name(old_column_name, table_info)

        new_column_name = request_data['newColumnName']
        validator.validate_new_column_name(new_column_name,
                                           table_info.table.columns)

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )


def validate_delete_column_request(request_data) -> Optional[Response]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)

        table_name = request_data['tableName']
        validator.validate_existed_table_name(table_name, all_tables_info)

        column_name = request_data['columnName']
        table_info = all_tables_info[table_name]
        validator.validate_existed_column_name(column_name, table_info)

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )


def validate_input_cell_data_request(request_data) -> Optional[Response]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)

        table_name = request_data['tableName']
        validator.validate_existed_table_name(table_name, all_tables_info)

        old_column_name = request_data['columnName']
        table_info = all_tables_info[table_name]
        validator.validate_existed_column_name(old_column_name, table_info)

        row_index = request_data['rowIndex']
        validator.validate_row_index(row_index, table_info.num_rows)
        # new_value = request_data['newValue']

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )


def validate_filter_single_condition_request(request_data) \
        -> Optional[Response]:
    try:
        validator = InputValidator(**INPUT_VALIDATOR_CONFIG)

        table_name = request_data['tableName']
        validator.validate_existed_table_name(table_name, all_tables_info)

        column_name = request_data['columnName']
        table_info = all_tables_info[table_name]
        validator.validate_existed_column_name(column_name, table_info)

        condition = request_data['condition']
        validator.validate_filter_condition(condition)

        is_compare_column = request_data['isCompareColumn']
        validator.validate_is_compare_column(is_compare_column)

        compare_value = request_data['compareValue']
        validator.validate_compare_value(compare_value)
        if (is_compare_column):
            validator.validate_existed_column_name(compare_value, table_info)

        return None
    except InputValidationError as e:
        return create_error_response(
            e.status_code,
            e.message
        )

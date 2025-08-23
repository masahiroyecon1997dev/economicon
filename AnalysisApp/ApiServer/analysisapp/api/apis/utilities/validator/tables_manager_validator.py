from typing import List, Optional
import polars as pl
from .validator_utils import remove_one_string_copy
from .common_validators import (
    ValidationError,
    validate_required,
    validate_boolean,
    validate_number,
    validate_integer,
    validate_required_list,
    validate_list_length,
    validate_string_length,
    validate_invalid_chars,
    validate_table_duplicate,
    validate_table_exists,
    validate_column_duplicate,
    validate_column_exists,
    validate_numeric_range,
    validate_candidates,
    validate_file_path_exists,
    validate_directory_path_exists,
    validate_column_is_numeric
)
from .validation_config import (SUPPORTED_DISTRIBUTIONS,
                                TABLES_MANAGER_VALIDATOR_CONFIG,
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
    validate_table_duplicate(table_name, table_name_param, table_name_list)


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
    validate_required_list(columns, column_names_param)
    validate_list_length(columns, column_names_param, 'item')
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
        validate_column_duplicate(column, column_names_param,
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
    validate_column_duplicate(new_column_name, new_column_name_param, columns)


def validate_existed_table_name(
    table_name: str,
    table_name_list: List[str],
    table_name_param: str
) -> None:
    validate_required(table_name, table_name_param)
    validate_table_exists(table_name, table_name_param, table_name_list)


def validate_existed_column_name(
    column_name: str,
    column_name_list: List[str],
    column_names_param: str
) -> None:
    validate_required(column_name, column_names_param)
    validate_column_exists(column_name, column_names_param, column_name_list)


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


def validate_distribution_type(
    distribution_type: str,
    distribution_type_param: str
) -> None:
    validate_required(distribution_type, distribution_type_param)
    validate_candidates(
        distribution_type,
        distribution_type_param,
        SUPPORTED_DISTRIBUTIONS,
    )


def validate_calculation_expression(
    expression: str,
    calculation_expression_param: str
) -> None:
    validate_required(expression, calculation_expression_param)


def validate_existed_numeric_columns(
    column_names: List[str],
    column_name_list: List[str],
    df: pl.DataFrame,
    calculation_expression_param: str,
    column_names_param: str
) -> None:
    validate_list_length(column_names, calculation_expression_param, 'column')
    for col_name in column_names:
        validate_required(col_name, column_names_param)
        validate_column_exists(col_name, column_names_param, column_name_list)
        column_type = df[col_name].dtype
        validate_column_is_numeric(col_name, column_names_param, column_type)


def validate_distribution_params(
    distribution_type: str,
    params: dict
) -> None:
    """分布ごとのパラメータを検証"""

    match distribution_type:
        case 'uniform':
            validate_number(params['low'], 'low')
            validate_number(params['high'], 'high')
            if params['low'] >= params['high']:
                raise ValidationError("For uniform distribution, "
                                      "'low' must be less than 'high'")
        case 'exponential':
            validate_number(params['scale'], 'scale')
            if params['scale'] <= 0:
                raise ValidationError("For exponential distribution, "
                                      "'scale' must be positive")
        case 'normal':
            validate_number(params['loc'], 'loc')
            validate_number(params['scale'], 'scale')
            if params['scale'] <= 0:
                raise ValidationError("For normal distribution, "
                                      "'scale' must be positive")
        case 'gamma':
            validate_number(params['shape'], 'shape')
            validate_number(params['scale'], 'scale')
            if params['shape'] <= 0 or params['scale'] <= 0:
                raise ValidationError("For gamma distribution, "
                                      "'shape' and 'scale' must be "
                                      "positive")
        case 'beta':
            validate_number(params['a'], 'a')
            validate_number(params['b'], 'b')
            if params['a'] <= 0 or params['b'] <= 0:
                raise ValidationError("For beta distribution, "
                                      "'a' and 'b' must be positive")
        case 'weibull':
            validate_number(params['a'], 'a')
            if params['a'] <= 0:
                raise ValidationError("For weibull distribution, "
                                      "'a' must be positive")
        case 'lognormal':
            validate_number(params['mean'], 'mean')
            validate_number(params['sigma'], 'sigma')
            if params['sigma'] <= 0:
                raise ValidationError("For lognormal distribution, "
                                      "'sigma' must be positive")
        case 'binomial':
            validate_integer(params['n'], 'n')
            validate_number(params['p'], 'p')
            if params['n'] <= 0:
                raise ValidationError("For binomial distribution, "
                                      "'n' must be positive")
            if not (0 <= params['p'] <= 1):
                raise ValidationError("For binomial distribution, "
                                      "'p' must be between 0 and 1")
        case 'bernoulli':
            validate_number(params['p'], 'p')
            if not (0 <= params['p'] <= 1):
                raise ValidationError("For bernoulli distribution, "
                                      "'p' must be between 0 and 1")
        case 'poisson':
            validate_number(params['lam'], 'lam')
            if params['lam'] <= 0:
                raise ValidationError("For poisson distribution, "
                                      "'lam' must be positive")
        case 'geometric':
            validate_number(params['p'], 'p')
            if not (0 < params['p'] <= 1):
                raise ValidationError("For geometric distribution, "
                                      "'p' must be between 0 and 1 "
                                      "(exclusive of 0)")
        case 'hypergeometric':
            validate_integer(params['N'], 'N')
            validate_integer(params['K'], 'K')
            validate_integer(params['n'], 'n')
            if params['N'] <= 0 or params['K'] <= 0 or params['n'] <= 0:
                raise ValidationError("For hypergeometric "
                                      "distribution, 'N', 'K', "
                                      "and 'n' must be positive")
            if params['K'] > params['N']:
                raise ValidationError("For hypergeometric "
                                      "distribution, 'K' "
                                      "must not exceed 'N'")
            if params['n'] > params['N']:
                raise ValidationError("For hypergeometric "
                                      "distribution, 'n' "
                                      "must not exceed 'N'")

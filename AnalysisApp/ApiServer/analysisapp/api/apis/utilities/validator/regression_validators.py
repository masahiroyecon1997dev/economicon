from typing import List, Optional
from .validator_utils import remove_one_string_copy
import polars as pl
from .common_validators import (
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
    validate_directory_path,
    validate_column_is_numeric
)
from ..validator.validation_config import (
    SUPPORTED_DISTRIBUTIONS)


class RegressionValidator:
    def __init__(
        self,
        param_names: Optional[dict] = None,
    ):
        self.param_names = param_names or {
            'table_name': 'tableName',
            'column_names': 'columnName'
        }

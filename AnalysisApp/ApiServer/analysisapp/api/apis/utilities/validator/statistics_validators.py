from typing import List, Optional
from .validator_utils import remove_one_string_copy
import polars as pl
from .common_validators import (
    validate_required,
    validate_required_list
)
from .validation_config import (
    SUPPORTED_DISTRIBUTIONS
)


class RegressionValidator:
    def __init__(
        self,
        param_names: Optional[dict] = None,
    ):
        self.param_names = param_names or {
            'table_name': 'tableName',
            'column_names': 'columnName'
        }

    def validate_explanatory_variables(
        self,
        explanatory_variables: List[str],
        dependent_variable: str
    ) -> None:
        for variable in explanatory_variables:
            if variable not in self.param_names.values():
                raise ValueError(f"Invalid explanatory variable: {variable}")

    def validate_dependent_variable(self, dependent_variable: str) -> None:
        if dependent_variable not in self.param_names.values():
            raise ValueError(f"Invalid dependent variable: {dependent_variable}")

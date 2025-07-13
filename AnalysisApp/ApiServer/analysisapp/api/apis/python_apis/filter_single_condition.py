import polars as pl
from typing import Dict
from django.utils.translation import gettext as _
from ..data.tables_info import TableInfo, all_tables_info
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..utilities.validator.common_validators import ValidationError
from .common_api_class import (AbstractApi, ApiError)


class FilterSingleCondition(AbstractApi):
    """
    """
    def __init__(self, new_table_name: str, table_name: str,
                 column_name: str, condition: str,
                 is_compare_column: str, compare_value: str):
        self.new_table_name = new_table_name
        self.table_name = table_name
        self.column_name = column_name
        self.condition = condition
        self.is_compare_column = is_compare_column
        self.compare_value = compare_value
        self.param_names = {
            'new_table_name': 'newTableName',
            'table_name': 'tableName',
            'column_names': 'columnName',
            'condition': 'condition',
            'is_compare_column': 'isCompareColumn',
            'compare_value': 'compareValue',
        }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            validator.validate_new_table_name(self.new_table_name,
                                              all_tables_info)
            validator.validate_existed_table_name(self.table_name,
                                                  all_tables_info)
            table_info = all_tables_info[self.table_name]
            validator.validate_existed_column_name(self.column_name,
                                                   table_info)
            validator.validate_filter_condition(self.condition)
            validator.validate_is_compare_column(self.is_compare_column)
            validator.validate_compare_value(self.compare_value)
            if self.is_compare_column == 'true':
                validator.validate_existed_column_name(self.compare_value,
                                                       table_info)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            df = all_tables_info[self.table_name].table

            match self.condition:
                case 'equals':
                    filtered_df = df.filter(
                        pl.col(self.column_name) == (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'notEquals':
                    filtered_df = df.filter(
                        pl.col(self.column_name) != (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'greaterThan':
                    filtered_df = df.filter(
                        pl.col(self.column_name) > (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'greaterThanOrEquals':
                    filtered_df = df.filter(
                        pl.col(self.column_name) >= (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'lessThan':
                    filtered_df = df.filter(
                        pl.col(self.column_name) < (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'lessThanOrEquals':
                    filtered_df = df.filter(
                        pl.col(self.column_name) <= (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case _:
                    raise ValidationError(_('Invalid condition specified'))

            table_info = TableInfo(self.new_table_name, filtered_df)
            all_tables_info[self.new_table_name] = table_info
            result = {'tableName': self.new_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "filter processing")
            raise ApiError(message) from e


def filter_single_condition(
    new_table_name: str, table_name: str, column_name: str,
    condition: str, is_compare_column: str, compare_value: str
) -> Dict:
    api = FilterSingleCondition(
        new_table_name, table_name, column_name, condition,
        is_compare_column, compare_value
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result


from typing import Dict, List
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config import (
    INPUT_VALIDATOR_CONFIG,
)
from ..data.tables_info import TableInfo, all_tables_info
from .common_api_class import AbstractApi, ApiError


class CreateJoinTable(AbstractApi):

    """結合テーブル作成APIのPythonロジック"""
    def __init__(
        self,
        join_table_name: str,
        left_table_name: str,
        right_table_name: str,
        left_key_column_names: List[str],
        right_key_column_names: List[str],
        join_type: str,
    ):
        self.join_table_name = join_table_name
        self.left_table_name = left_table_name
        self.right_table_name = right_table_name
        self.left_key_column_names = left_key_column_names
        self.right_key_column_names = right_key_column_names
        self.join_type = join_type
        self.param_names = {
            'table_name': 'joinTableName',
            'left_table_name': 'leftTableName',
            'right_table_name': 'rightTableName',
            'column_names': 'leftKeyColumnNames',
            'new_column_name': 'rightKeyColumnNames',
            'join_type': 'joinType',
        }

    def validate(self):
        try:
            validator = InputValidator(
                param_names=self.param_names, **INPUT_VALIDATOR_CONFIG
            )
            validator.validate_new_table_name(
                self.join_table_name, all_tables_info
            )
            validator.param_names['table_name'] = 'leftTableName'
            validator.validate_existed_table_name(
                self.left_table_name, all_tables_info
            )
            validator.param_names['table_name'] = 'rightTableName'
            validator.validate_existed_table_name(
                self.right_table_name, all_tables_info
            )
            left_table_info = all_tables_info[self.left_table_name]
            for left_key_column_name in self.left_key_column_names:
                validator.param_names['column_names'] = 'leftKeyColumnNames'
                validator.validate_existed_column_name(
                    left_key_column_name, left_table_info
                )
            right_table_info = all_tables_info[self.right_table_name]
            for right_key_column_name in self.right_key_column_names:
                validator.param_names['column_names'] = 'rightKeyColumnNames'
                validator.validate_existed_column_name(
                    right_key_column_name, right_table_info
                )
            validator.validate_join_type(self.join_type)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            left_df = all_tables_info[self.left_table_name].table
            right_df = all_tables_info[self.right_table_name].table
            match self.join_type:
                case 'inner':
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='inner',
                    )
                case 'left':
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='left',
                    )
                case 'right':
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='right',
                    )
                case 'outer':
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='full',
                        coalesce=True,
                        maintain_order='left',
                    )
                case _:
                    raise ApiError("Invalid join type specified.")
            table_info = TableInfo(
                table_name=self.join_table_name, table=df
            )
            all_tables_info[self.join_table_name] = table_info
            result = {'tableName': self.join_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "join table creation processing"
            )
            raise ApiError(message) from e


def create_join_table(
    join_table_name: str,
    left_table_name: str,
    right_table_name: str,
    left_key_column_names: List[str],
    right_key_column_names: List[str],
    join_type: str,
) -> Dict:
    api = CreateJoinTable(
        join_table_name, left_table_name, right_table_name,
        left_key_column_names, right_key_column_names, join_type
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

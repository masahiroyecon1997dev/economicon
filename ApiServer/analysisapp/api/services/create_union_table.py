from typing import Dict, List

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_columns, validate_existed_tables, validate_new_table_name)
from .abstract_api import AbstractApi, ApiError


class CreateUnionTable(AbstractApi):
    """
    繝ｦ繝九が繝ｳ繝・・繝悶Ν菴懈・API縺ｮPython繝ｭ繧ｸ繝・け

    隍・焚縺ｮ繝・・繝悶Ν繧呈欠螳壹＆繧後◆蛻励〒繝ｦ繝九が繝ｳ・育ｵ仙粋・峨＠縲∵眠縺励＞繝・・繝悶Ν繧剃ｽ懈・縺励∪縺吶・    縺吶∋縺ｦ縺ｮ繝・・繝悶Ν縺ｫ蜈ｱ騾壹☆繧句・蜷阪ｒ謖・ｮ壹＠縺ｦ縲√◎繧後ｉ縺ｮ陦後ｒ邨仙粋縺励∪縺吶・    """
    def __init__(
        self,
        union_table_name: str,
        table_names: List[str],
        column_names: List[str],
    ):
        self.tables_manager = TablesManager()
        # 繝ｦ繝九が繝ｳ蠕後・繝・・繝悶Ν蜷・        self.union_table_name = union_table_name
        # 繝ｦ繝九が繝ｳ縺吶ｋ繝・・繝悶Ν蜷阪Μ繧ｹ繝・        self.table_names = table_names
        # 繝ｦ繝九が繝ｳ縺吶ｋ蛻怜錐繝ｪ繧ｹ繝・        self.column_names = column_names
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'union_table_name': 'unionTableName',
            'table_names': 'tableNames',
            'column_names': 'columnNames',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            table_name_list = self.tables_manager.get_table_name_list()

            # 譁ｰ縺励＞繝・・繝悶Ν蜷阪・驥崎､・メ繧ｧ繝・け
            validate_new_table_name(
                self.union_table_name,
                table_name_list,
                self.param_names['union_table_name']
            )

            validate_existed_tables(
                self.table_names,
                table_name_list,
                self.param_names['table_names']
            )

            # 縺吶∋縺ｦ縺ｮ繝・・繝悶Ν縺ｧ謖・ｮ壹＆繧後◆蛻励′蟄伜惠縺吶ｋ縺薙→繧偵メ繧ｧ繝・け
            for table_name in self.table_names:
                table_column_name_list = \
                    self.tables_manager.get_column_name_list(
                        table_name
                    )
                validate_existed_columns(
                    self.column_names,
                    table_column_name_list,
                    self.param_names['column_names']
                )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 繝・・繝悶Ν繝ｦ繝九が繝ｳ蜃ｦ逅・        try:
            # 蜷・ユ繝ｼ繝悶Ν縺九ｉ謖・ｮ壹＆繧後◆蛻励・縺ｿ繧帝∈謚槭＠縺ｦ繝・・繧ｿ繝輔Ξ繝ｼ繝縺ｮ繝ｪ繧ｹ繝医ｒ菴懈・
            dataframes = []
            for table_name in self.table_names:
                df = self.tables_manager.get_table(table_name).table
                # 謖・ｮ壹＆繧後◆蛻励・縺ｿ繧帝∈謚・                selected_df = df.select(self.column_names)
                dataframes.append(selected_df)

            # 縺吶∋縺ｦ縺ｮ繝・・繧ｿ繝輔Ξ繝ｼ繝繧偵Θ繝九が繝ｳ・育ｸｦ譁ｹ蜷代↓邨仙粋・・            union_df = pl.concat(dataframes, how="vertical")

            # 譁ｰ縺励＞繝・・繝悶Ν諠・ｱ繧剃ｿ晏ｭ・            created_table_name = self.tables_manager.store_table(
                self.union_table_name, union_df
            )

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': created_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "union table creation processing"
            )
            raise ApiError(message) from e


def create_union_table(
    union_table_name: str,
    table_names: List[str],
    column_names: List[str],
) -> Dict:
    api = CreateUnionTable(
        union_table_name, table_names, column_names
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

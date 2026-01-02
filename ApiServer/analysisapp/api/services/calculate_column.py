import polars as pl
import re
from .django_compat import gettext as _
from typing import Dict, List
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name,
    validate_new_column_name,
    validate_calculation_expression,
    validate_existed_numeric_columns
)
from .data.tables_manager import TablesManager
from .abstract_api import (AbstractApi, ApiError)


class CalculateColumn(AbstractApi):
    """
    繝・・繝悶Ν縺ｮ蛻怜酔螢ｫ縺ｨ謨ｰ蛟､縺ｮ險育ｮ励ｒ陦後＞縲∫ｵ先棡蛻励ｒ霑ｽ蜉縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｫ險育ｮ怜ｼ上↓蝓ｺ縺･縺・※譁ｰ縺励＞蛻励ｒ霑ｽ蜉縺励∪縺吶・    險育ｮ怜ｼ上・蛻怜錐繧・蛻怜錐>縺ｮ蠖｢蠑上〒謖・ｮ壹＠縲∝屁蜑・ｼ皮ｮ励→縺九▲縺薙ｒ繧ｵ繝昴・繝医＠縺ｾ縺吶・    """
    def __init__(self, table_name: str, new_column_name: str,
                 calculation_expression: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.new_column_name = new_column_name
        self.calculation_expression = calculation_expression
        self.param_names = {
                'table_name': 'tableName',
                'new_column_name': 'newColumnName',
                'calculation_expression': 'calculationExpression',
                'column_name_in_calculation_expression':
                'columnName in calculationExpression'
            }

    def _extract_column_names(self, expression: str) -> List[str]:
        """
        險育ｮ怜ｼ上°繧牙・蜷阪ｒ謚ｽ蜃ｺ縺吶ｋ
        """
        # pl.col("蛻怜錐")縺ｮ繝代ち繝ｼ繝ｳ縺ｧ蛻怜錐繧呈歓蜃ｺ
        pattern = r'pl\.col\("([^"]+)"\)'
        column_names = re.findall(pattern, expression)
        return list(set(column_names))  # 驥崎､・ｒ髯､蜴ｻ

    def validate(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 譁ｰ縺励＞蛻怜錐縺ｮ讀懆ｨｼ
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names['new_column_name']
            )

            # 險育ｮ怜ｼ上′遨ｺ縺ｧ縺ｪ縺・％縺ｨ繧呈､懆ｨｼ
            expression = self.calculation_expression.strip()
            validate_calculation_expression(
                expression,
                self.param_names['calculation_expression']
            )

            # 險育ｮ怜ｼ上°繧牙・蜷阪ｒ謚ｽ蜃ｺ縺励※蟄伜惠繝√ぉ繝・け
            referenced_columns = self._extract_column_names(
                self.calculation_expression,

            )
            df_schema = self.tables_manager.get_column_info_list(
                self.table_name)
            validate_existed_numeric_columns(
                referenced_columns,
                column_name_list,
                df_schema,
                self.param_names['calculation_expression'],
                self.param_names['column_name_in_calculation_expression']
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # Polars縺ｮ蠑上ｒ隧穂ｾ｡
            try:
                # 螳牙・縺ｪeval迺ｰ蠅・〒Polars蠑上ｒ隧穂ｾ｡
                safe_globals = {'pl': pl}
                polars_expr = eval(self.calculation_expression, safe_globals)

                # 譁ｰ縺励＞蛻励ｒ險育ｮ励＠縺ｦ霑ｽ蜉
                df_with_new_col = df.with_columns(
                    polars_expr.alias(self.new_column_name))

            except Exception as e:
                raise ValidationError(
                    f"Invalid calculation expression: {str(e)}")

            # 繝・・繝悶Ν繧呈峩譁ｰ
            self.tables_manager.update_table(self.table_name, df_with_new_col)

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': self.table_name,
                      'columnName': self.new_column_name}
            return result
        except ValidationError:
            raise
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "column calculation processing")
            raise ApiError(message) from e


def calculate_column(table_name: str,
                     new_column_name: str,
                     calculation_expression: str) -> Dict:
    api = CalculateColumn(table_name, new_column_name, calculation_expression)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result


from typing import Dict, List

from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name,
    validate_join_type, validate_new_table_name)
from .abstract_api import AbstractApi, ApiError


class CreateJoinTable(AbstractApi):
    """
    邨仙粋繝・・繝悶Ν菴懈・API縺ｮPython繝ｭ繧ｸ繝・け

    莠後▽縺ｮ繝・・繝悶Ν繧呈欠螳壹＆繧後◆繧ｭ繝ｼ縺ｧ邨仙粋縺励∵眠縺励＞繝・・繝悶Ν繧剃ｽ懈・縺励∪縺吶・    蜀・Κ邨仙粋縲∝ｷｦ邨仙粋縲∝承邨仙粋縲∝ｮ悟・螟夜Κ邨仙粋縺ｫ蟇ｾ蠢懊＠縺ｦ縺・∪縺吶・    """
    def __init__(
        self,
        join_table_name: str,
        left_table_name: str,
        right_table_name: str,
        left_key_column_names: List[str],
        right_key_column_names: List[str],
        join_type: str,
    ):
        self.tables_manager = TablesManager()
        # 邨仙粋蠕後・繝・・繝悶Ν蜷・        self.join_table_name = join_table_name
        # 蟾ｦ繝・・繝悶Ν蜷・        self.left_table_name = left_table_name
        # 蜿ｳ繝・・繝悶Ν蜷・        self.right_table_name = right_table_name
        # 蟾ｦ繝・・繝悶Ν縺ｮ繧ｭ繝ｼ蛻怜錐繝ｪ繧ｹ繝・        self.left_key_column_names = left_key_column_names
        # 蜿ｳ繝・・繝悶Ν縺ｮ繧ｭ繝ｼ蛻怜錐繝ｪ繧ｹ繝・        self.right_key_column_names = right_key_column_names
        # 邨仙粋繧ｿ繧､繝暦ｼ・nner, left, right, outer・・        self.join_type = join_type
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'table_name': 'joinTableName',
            'left_table_name': 'leftTableName',
            'right_table_name': 'rightTableName',
            'left_key_column_names': 'leftKeyColumnNames',
            'right_key_column_names': 'rightKeyColumnNames',
            'join_type': 'joinType',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            # 譁ｰ縺励＞繝・・繝悶Ν蜷阪・驥崎､・メ繧ｧ繝・け
            validate_new_table_name(
                self.join_table_name,
                table_name_list,
                self.param_names['table_name']
            )
            # 蟾ｦ繝・・繝悶Ν縺ｮ蟄伜惠繝√ぉ繝・け
            validate_existed_table_name(
                self.left_table_name,
                table_name_list,
                self.param_names['left_table_name']
            )
            # 蜿ｳ繝・・繝悶Ν縺ｮ蟄伜惠繝√ぉ繝・け
            validate_existed_table_name(
                self.right_table_name,
                table_name_list,
                self.param_names['right_table_name']
            )
            # 蟾ｦ繝・・繝悶Ν縺ｮ繧ｭ繝ｼ蛻励・蟄伜惠繝√ぉ繝・け
            left_table_column_name_list = TablesManager().get_column_name_list(
                self.left_table_name
            )
            for left_key_column_name in self.left_key_column_names:
                validate_existed_column_name(
                    left_key_column_name,
                    left_table_column_name_list,
                    self.param_names['left_key_column_names']
                )
            # 蜿ｳ繝・・繝悶Ν縺ｮ繧ｭ繝ｼ蛻励・蟄伜惠繝√ぉ繝・け
            right_table_column_name_list = \
                TablesManager().get_column_name_list(
                    self.right_table_name
                )
            for right_key_column_name in self.right_key_column_names:
                validate_existed_column_name(
                    right_key_column_name,
                    right_table_column_name_list,
                    self.param_names['right_key_column_names']
                )
            # 邨仙粋繧ｿ繧､繝励・螯･蠖捺ｧ繝√ぉ繝・け
            validate_join_type(
                self.join_type,
                self.param_names['join_type']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 繝・・繝悶Ν邨仙粋蜃ｦ逅・        try:
            # 蟾ｦ繝・・繝悶Ν縺ｮ繝・・繧ｿ繝輔Ξ繝ｼ繝繧貞叙蠕・            left_df = self.tables_manager.get_table(
                self.left_table_name).table
            # 蜿ｳ繝・・繝悶Ν縺ｮ繝・・繧ｿ繝輔Ξ繝ｼ繝繧貞叙蠕・            right_df = self.tables_manager.get_table(
                self.right_table_name).table
            # 邨仙粋繧ｿ繧､繝励↓蠢懊§縺ｦ邨仙粋蜃ｦ逅・ｒ螳溯｡・            match self.join_type:
                case 'inner':
                    # 蜀・Κ邨仙粋
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='inner',
                    )
                case 'left':
                    # 蟾ｦ邨仙粋
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='left',
                    )
                case 'right':
                    # 蜿ｳ邨仙粋
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='right',
                    )
                case 'outer':
                    # 螳悟・螟夜Κ邨仙粋
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
            # 譁ｰ縺励＞繝・・繝悶Ν諠・ｱ繧剃ｿ晏ｭ・            created_table_name = self.tables_manager.store_table(
                self.join_table_name, df
            )
            # 邨先棡繧定ｿ斐☆
            result = {'tableName': created_table_name}
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

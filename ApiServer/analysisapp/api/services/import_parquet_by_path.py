from typing import Dict

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.file_validators import validate_file_path
from ..utils.validator.tables_manager_validator import \
    validate_new_table_name
from .abstract_api import AbstractApi, ApiError


class ImportParquetByPath(AbstractApi):
    """
    PARQUET繝輔ぃ繧､繝ｫ繝代せ謖・ｮ壹〒繝・・繧ｿ繧偵う繝ｳ繝昴・繝医＠縺ｦ繝・・繝悶Ν繧剃ｽ懈・縺吶ｋAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝代せ縺ｮPARQUET繝輔ぃ繧､繝ｫ繧定ｧ｣譫舌＠縲∵欠螳壹＆繧後◆繝・・繝悶Ν蜷阪〒逋ｻ骭ｲ縺励∪縺吶・    """

    def __init__(self, file_path: str, table_name: str):
        # 繝・・繝悶Ν繝槭ロ繝ｼ繧ｸ繝｣繝ｼ縺ｮ蛻晄悄蛹・        self.tables_manager = TablesManager()
        # 繝輔ぃ繧､繝ｫ繝代せ
        self.file_path = file_path
        # 繝・・繝悶Ν蜷・        self.table_name = table_name
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'file_path': 'filePath',
            'table_name': 'tableName',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            validate_file_path(
                self.file_path,
                self.param_names['file_path']
            )
            table_name_list = self.tables_manager.get_table_name_list()
            # 繝・・繝悶Ν蜷阪・繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
            validate_new_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # PARQUET繝輔ぃ繧､繝ｫ縺ｮ繧､繝ｳ繝昴・繝亥・逅・        try:
            # PARQUET繝輔ぃ繧､繝ｫ繧単olars繝・・繧ｿ繝輔Ξ繝ｼ繝縺ｫ螟画鋤
            df = pl.read_parquet(self.file_path)

            # 繝・・繝悶Ν繧剃ｽ懈・
            created_table_name = self.tables_manager.store_table(
                self.table_name, df)

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': created_table_name}
            return result

        except pl.exceptions.NoDataError as e:
            message = _("The PARQUET file is empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.exceptions.ComputeError as e:
            message = _("Failed to parse PARQUET file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "PARQUET processing")
            raise ApiError(message) from e


def import_parquet_by_path(file_path: str, table_name: str) -> Dict:
    """
    PARQUET繝輔ぃ繧､繝ｫ繝代せ縺九ｉ繝・・繧ｿ繧偵う繝ｳ繝昴・繝医＠縺ｦ繝・・繝悶Ν繧剃ｽ懈・縺吶ｋ髢｢謨ｰ

    Args:
        file_path: PARQUET繝輔ぃ繧､繝ｫ縺ｮ繝代せ
        table_name: 菴懈・縺吶ｋ繝・・繝悶Ν蜷・
    Returns:
        菴懈・縺輔ｌ縺溘ユ繝ｼ繝悶Ν蜷阪ｒ蜷ｫ繧霎樊嶌
    """
    api = ImportParquetByPath(file_path, table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # API繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺溷ｴ蜷医・縺昴・縺ｾ縺ｾ蜀阪せ繝ｭ繝ｼ
        raise e
    return result

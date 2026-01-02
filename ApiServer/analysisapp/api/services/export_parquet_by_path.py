import os
from typing import Dict

from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.file_validators import (validate_directory_path,
                                                   validate_file_name)
from ..utils.validator.tables_manager_validator import \
    validate_existed_table_name
from .abstract_api import AbstractApi, ApiError


class ExportParquetByPath(AbstractApi):
    """
    繝・・繝悶Ν繧単ARQUET繝輔ぃ繧､繝ｫ繝代せ謖・ｮ壹〒繧ｨ繧ｯ繧ｹ繝昴・繝医☆繧帰PI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν蜷阪・繝・・繧ｿ繧呈欠螳壹＆繧後◆繝代せ縺ｫPARQUET繝輔ぃ繧､繝ｫ縺ｨ縺励※蜃ｺ蜉帙＠縺ｾ縺吶・    """

    def __init__(self, table_name: str, directory_path: str,
                 file_name: str):
        # 繝・・繝悶Ν繝槭ロ繝ｼ繧ｸ繝｣繝ｼ縺ｮ蛻晄悄蛹・        self.tables_manager = TablesManager()
        # 繝・・繝悶Ν蜷・        self.table_name = table_name
        # 繝・ぅ繝ｬ繧ｯ繝医Μ繝代せ
        self.directory_path = directory_path
        # 繝輔ぃ繧､繝ｫ蜷・        self.file_name = file_name
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'table_name': 'tableName',
            'directory_path': 'directoryPath',
            'file_name': 'fileName',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            # 繝・・繝悶Ν蜷阪・繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 繝・ぅ繝ｬ繧ｯ繝医Μ繝代せ縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
            validate_directory_path(
                self.directory_path,
                self.param_names['directory_path']
            )

            # 繝輔ぃ繧､繝ｫ蜷阪・繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
            validate_file_name(
                self.file_name,
                self.param_names['file_name']
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # PARQUET繝輔ぃ繧､繝ｫ縺ｮ繧ｨ繧ｯ繧ｹ繝昴・繝亥・逅・        try:
            # 繝・・繝悶Ν繧貞叙蠕・            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            file_path = os.path.join(self.directory_path, self.file_name)

            # PARQUET繝輔ぃ繧､繝ｫ縺ｫ譖ｸ縺崎ｾｼ縺ｿ
            df.write_parquet(file_path)

            # 邨先棡繧定ｿ斐☆
            result = {'filePath': file_path}
            return result

        except KeyError as e:
            message = _("Table does not exist: {}").format(self.table_name)
            raise ApiError(message) from e
        except PermissionError as e:
            message = _("Permission denied: Cannot write to "
                        "the specified path.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "PARQUET export processing")
            raise ApiError(message) from e


def export_parquet_by_path(table_name: str,
                           directory_path: str,
                           file_name: str) -> Dict:
    """
    繝・・繝悶Ν繧単ARQUET繝輔ぃ繧､繝ｫ繝代せ縺ｫ蜃ｺ蜉帙☆繧矩未謨ｰ

    Args:
        table_name: 繧ｨ繧ｯ繧ｹ繝昴・繝医☆繧九ユ繝ｼ繝悶Ν蜷・        directory_path: 蜃ｺ蜉帙☆繧九ョ繧｣繝ｬ繧ｯ繝医Μ繝代せ
        file_name: 蜃ｺ蜉帙☆繧輝ARQUET繝輔ぃ繧､繝ｫ蜷・
    Returns:
        蜃ｺ蜉帙＆繧後◆繝輔ぃ繧､繝ｫ繝代せ繧貞性繧霎樊嶌
    """
    api = ExportParquetByPath(table_name, directory_path, file_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # API繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺溷ｴ蜷医・縺昴・縺ｾ縺ｾ蜀阪せ繝ｭ繝ｼ
        raise e
    return result

import io
from typing import BinaryIO, Dict

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.create_table_name import create_table_name_by_file_name
from ..utils.validator.common_validators import ValidationError
from .abstract_api import AbstractApi, ApiError


class ImportCsvByFile(AbstractApi):
    """
    CSV繝輔ぃ繧､繝ｫ縺九ｉ繝・・繧ｿ繧偵う繝ｳ繝昴・繝医＠縺ｦ繝・・繝悶Ν繧剃ｽ懈・縺吶ｋAPI繧ｯ繝ｩ繧ｹ

    繧｢繝・・繝ｭ繝ｼ繝峨＆繧後◆CSV繝輔ぃ繧､繝ｫ繧定ｧ｣譫舌＠縲∵眠縺励＞繝・・繝悶Ν縺ｨ縺励※逋ｻ骭ｲ縺励∪縺吶・    繝・・繝悶Ν蜷阪・繝輔ぃ繧､繝ｫ蜷阪°繧芽・蜍慕函謌舌＆繧後∪縺吶・    """

    def __init__(self, file_data: BinaryIO, file_name: str):
        # 繝・・繝悶Ν繝槭ロ繝ｼ繧ｸ繝｣繝ｼ縺ｮ蛻晄悄蛹・        self.tables_manager = TablesManager()
        # 繝輔ぃ繧､繝ｫ繝・・繧ｿ
        self.file_data = file_data
        # 繝輔ぃ繧､繝ｫ蜷・        self.file_name = file_name
        # 閾ｪ蜍慕函謌舌＆繧後ｋ繝・・繝悶Ν蜷・        table_name_list = self.tables_manager.get_table_name_list()
        self.table_name = create_table_name_by_file_name(file_name,
                                                         table_name_list)
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'file': 'file',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            # 繝輔ぃ繧､繝ｫ繝・・繧ｿ縺ｮ蝓ｺ譛ｬ繝√ぉ繝・け
            if not self.file_data or not self.file_name:
                raise ValidationError(_("File data or file name is missing"))

            # CSV繝輔ぃ繧､繝ｫ縺ｮ諡｡蠑ｵ蟄舌メ繧ｧ繝・け
            if not self.file_name.lower().endswith('.csv'):
                raise ValidationError(_("File must be a CSV file"))

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # CSV繝輔ぃ繧､繝ｫ縺ｮ繧､繝ｳ繝昴・繝亥・逅・        try:
            # CSV繝輔ぃ繧､繝ｫ繧単olars繝・・繧ｿ繝輔Ξ繝ｼ繝縺ｫ螟画鋤
            df = pl.read_csv(io.BytesIO(self.file_data.read()))

            # 繝・・繝悶Ν繧剃ｽ懈・
            self.tables_manager.store_table(self.table_name, df)

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': self.table_name}
            return result

        except pl.exceptions.NoDataError as e:
            message = _("The uploaded CSV file is "
                        "empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.exceptions.ComputeError as e:
            message = _("Failed to parse CSV file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during CSV processing")
            raise ApiError(message) from e


def import_csv_by_file(file_data: BinaryIO, file_name: str) -> Dict:
    """
    CSV繝輔ぃ繧､繝ｫ縺九ｉ繝・・繧ｿ繧偵う繝ｳ繝昴・繝医＠縺ｦ繝・・繝悶Ν繧剃ｽ懈・縺吶ｋ髢｢謨ｰ

    Args:
        file_data: CSV繝輔ぃ繧､繝ｫ縺ｮ繝舌う繝翫Μ繝・・繧ｿ
        file_name: CSV繝輔ぃ繧､繝ｫ縺ｮ蜷榊燕

    Returns:
        菴懈・縺輔ｌ縺溘ユ繝ｼ繝悶Ν蜷阪ｒ蜷ｫ繧霎樊嶌
    """
    api = ImportCsvByFile(file_data, file_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # API繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺溷ｴ蜷医・縺昴・縺ｾ縺ｾ蜀阪せ繝ｭ繝ｼ
        raise e
    return result

import polars as pl
from django.utils.translation import gettext as _
from typing import Dict, List
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import Validator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class DescriptiveStatistics(AbstractApi):
    """
    指定されたテーブルの列の記述統計を計算するためのAPIクラス

    指定されたテーブルの指定された列に対して、要求された記述統計を計算します。
    サポートする統計: 平均、最頻値、中央値、分散、標準偏差、範囲、四分位範囲
    """

    # 利用可能な統計の種類を定義
    AVAILABLE_STATISTICS = {
        'mean': '平均',
        'mode': '最頻値',
        'median': '中央値',
        'variance': '分散',
        'std': '標準偏差',
        'range': '範囲',
        'iqr': '四分位範囲'
    }

    def __init__(self, table_name: str, column_name: str, statistics: List[str]):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.column_name = column_name
        self.statistics = statistics
        self.param_names = {
            'table_name': 'tableName',
            'column_names': 'columnName',
            'statistics': 'statistics',
        }

    def validate(self):
        try:
            validator = Validator(param_names=self.param_names,
                                  **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.tables_manager.get_table_name_list()
            validator.validate_existed_table_name(self.table_name,
                                                  table_name_list)
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validator.validate_existed_column_name(self.column_name,
                                                   column_name_list)

            # 統計の種類をバリデーション
            for stat in self.statistics:
                if stat not in self.AVAILABLE_STATISTICS:
                    raise ValidationError(
                        f"statistics '{stat}' is not supported. "
                        f"Available: {list(self.AVAILABLE_STATISTICS.keys())}")

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # 数値でない列の場合、一部の統計は計算できない
            numeric_only_stats = ['mean', 'variance', 'std', 'range', 'iqr']
            column_dtype = df[self.column_name].dtype
            is_numeric = column_dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                                         pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                                         pl.Float32, pl.Float64]

            results = {}

            for stat in self.statistics:
                if stat in numeric_only_stats and not is_numeric:
                    results[stat] = None
                    continue

                if stat == 'mean':
                    result_df = df.select(pl.col(self.column_name).mean())
                    results[stat] = float(result_df.item())
                elif stat == 'mode':
                    result_df = df.select(pl.col(self.column_name).mode())
                    if result_df.height > 0:
                        results[stat] = result_df.item(0, 0)
                    else:
                        results[stat] = None
                elif stat == 'median':
                    if is_numeric:
                        result_df = df.select(pl.col(self.column_name).median())
                        results[stat] = float(result_df.item())
                    else:
                        results[stat] = None
                elif stat == 'variance':
                    result_df = df.select(pl.col(self.column_name).var())
                    results[stat] = float(result_df.item())
                elif stat == 'std':
                    result_df = df.select(pl.col(self.column_name).std())
                    results[stat] = float(result_df.item())
                elif stat == 'range':
                    max_df = df.select(pl.col(self.column_name).max())
                    min_df = df.select(pl.col(self.column_name).min())
                    max_val = max_df.item()
                    min_val = min_df.item()
                    if max_val is not None and min_val is not None:
                        results[stat] = float(max_val - min_val)
                    else:
                        results[stat] = None
                elif stat == 'iqr':
                    q75_df = df.select(pl.col(self.column_name).quantile(0.75))
                    q25_df = df.select(pl.col(self.column_name).quantile(0.25))
                    q75 = q75_df.item()
                    q25 = q25_df.item()
                    if q75 is not None and q25 is not None:
                        results[stat] = float(q75 - q25)
                    else:
                        results[stat] = None

            # 結果を返す
            result = {
                'tableName': self.table_name,
                'columnName': self.column_name,
                'statistics': results
            }
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "descriptive statistics processing")
            raise ApiError(message) from e


def descriptive_statistics(table_name: str,
                           column_name_list: List[str],
                           statistics: List[str]) -> Dict:
    api = DescriptiveStatistics(table_name, column_name_list, statistics)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

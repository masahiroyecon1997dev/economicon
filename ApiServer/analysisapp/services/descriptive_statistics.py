from typing import Dict, List

import polars as pl
from ..i18n.translation import gettext as _

from .data.tables_store import TablesStore
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_store_validator import (
    validate_existed_column_name, validate_existed_table_name)
from .abstract_api import AbstractApi, ApiError


class DescriptiveStatistics(AbstractApi):
    """
    指定されたテーブルの列の記述統計を計算するためのAPIクラス

    指定されたテーブルの指定された列に対して、要求された記述統計を計算します。
    サポートする統計: 平均、最頻値、中央値、分散、標準偏差、範囲、四分位範囲
    """

    # 利用可能な統計の種類を定義
    AVAILABLE_STATISTICS = {
        'mean': 'Mean',
        'mode': 'Mode',
        'median': 'Median',
        'variance': 'Variance',
        'std': 'Standard Deviation',
        'range': 'Range',
        'iqr': 'Interquartile Range'
    }

    def __init__(self, table_name: str, column_name_list: List[str],
                 statistics: List[str]):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.column_name_list = column_name_list
        self.statistics = statistics
        self.param_names = {
            'table_name': 'tableName',
            'column_names': 'columnName',
            'statistics': 'statistics',
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name)
            for column_name in self.column_name_list:
                validate_existed_column_name(
                    column_name,
                    column_name_list,
                    self.param_names['column_names']
                )

            # 統計の種類をバリデーション
            if not self.statistics:
                raise ValidationError(
                    _("statistics is required"))
            for stat in self.statistics:
                if stat not in self.AVAILABLE_STATISTICS:
                    available = list(
                        self.AVAILABLE_STATISTICS.keys()
                    )
                    raise ValidationError(
                        _("statistics '{}'はサポートされていません。"
                          "利用可能: {}").format(
                            stat, available))

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # 数値でない列の場合、一部の統計は計算できない
            numeric_only_stats = ['mean', 'variance', 'std', 'range', 'iqr']

            result = {}

            for column_name in self.column_name_list:
                column_dtype = df[column_name].dtype
                is_numeric = column_dtype in [pl.Int8, pl.Int16, pl.Int32,
                                              pl.Int64, pl.UInt8, pl.UInt16,
                                              pl.UInt32, pl.UInt64, pl.Float32,
                                              pl.Float64]
                col_stats = {}

                for stat in self.statistics:
                    if stat in numeric_only_stats and not is_numeric:
                        col_stats[stat] = None
                        continue

                    if stat == 'mean':
                        result_df = df.select(pl.col(column_name).mean())
                        col_stats[stat] = float(result_df.item())
                    elif stat == 'mode':
                        result_df = df.select(pl.col(column_name).mode())
                        if result_df.height > 0:
                            col_stats[stat] = result_df.item(0, 0)
                        else:
                            col_stats[stat] = None
                    elif stat == 'median':
                        if is_numeric:
                            result_df = df.select(pl.col(column_name).median())
                            col_stats[stat] = float(result_df.item())
                        else:
                            col_stats[stat] = None
                    elif stat == 'variance':
                        result_df = df.select(pl.col(column_name).var())
                        col_stats[stat] = float(result_df.item())
                    elif stat == 'std':
                        result_df = df.select(pl.col(column_name).std())
                        col_stats[stat] = float(result_df.item())
                    elif stat == 'range':
                        max_df = df.select(pl.col(column_name).max())
                        min_df = df.select(pl.col(column_name).min())
                        max_val = max_df.item()
                        min_val = min_df.item()
                        if max_val is not None and min_val is not None:
                            col_stats[stat] = float(max_val - min_val)
                        else:
                            col_stats[stat] = None
                    elif stat == 'iqr':
                        q75_df = df.select(pl.col(column_name).quantile(0.75))
                        q25_df = df.select(pl.col(column_name).quantile(0.25))
                        q75 = q75_df.item()
                        q25 = q25_df.item()
                        if q75 is not None and q25 is not None:
                            col_stats[stat] = float(q75 - q25)
                        else:
                            col_stats[stat] = None

                result[column_name] = col_stats

            # 結果を返す
            result = {
                'tableName': self.table_name,
                'statistics': result
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
        raise ValueError(validation_error.message)
    result = api.execute()
    return result

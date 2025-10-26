import numpy as np
from scipy import stats
from django.utils.translation import gettext as _
from typing import Dict
from ..utilities.validator.common_validators import (
    ValidationError, validate_candidates
)
from ..utilities.validator.tables_manager_validator import (
    validate_existed_table_name,
    validate_existed_column_name
)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class ConfidenceInterval(AbstractApi):
    """
    指定されたテーブルの列の信頼区間を計算するためのAPIクラス

    指定されたテーブルの指定された列に対して、指定された統計の信頼区間を計算します。
    サポートする統計: 平均、中央値、比率、分散、標準偏差
    """

    # 利用可能な統計の種類を定義
    AVAILABLE_STATISTICS = {
        'mean': 'Mean',
        'median': 'Median',
        'proportion': 'Proportion',
        'variance': 'Variance',
        'std': 'Standard Deviation'
    }

    def __init__(self, table_name: str, column_name: str,
                 confidence_level: float, statistic_type: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.column_name = column_name
        self.confidence_level = confidence_level
        self.statistic_type = statistic_type
        self.param_names = {
            'table_name': 'tableName',
            'column_name': 'columnName',
            'confidence_level': 'confidenceLevel',
            'statistic_type': 'statisticType',
        }

    def validate(self):
        try:
            # テーブル名の検証
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 列名の検証
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_existed_column_name(
                self.column_name,
                column_name_list,
                self.param_names['column_name']
            )

            # 統計タイプの検証
            validate_candidates(
                self.statistic_type,
                self.param_names['statistic_type'],
                list(self.AVAILABLE_STATISTICS.keys())
            )

            # 信頼度レベルの検証
            if not isinstance(self.confidence_level, (int, float)):
                raise ValidationError("confidenceLevel must be a number")

            if not (0 < self.confidence_level < 1):
                raise ValidationError("confidenceLevel must be between 0 and 1")

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # 列のデータを取得
            column_data = df[self.column_name].drop_nulls()

            if column_data.len() == 0:
                raise ValidationError("Column contains no valid data")

            # データを numpy array に変換
            data_array = column_data.to_numpy()

            # 統計量と信頼区間を計算
            if self.statistic_type == 'mean':
                statistic_value, ci_lower, ci_upper = \
                    self._calculate_mean_ci(data_array)
            elif self.statistic_type == 'median':
                statistic_value, ci_lower, ci_upper = \
                    self._calculate_median_ci(data_array)
            elif self.statistic_type == 'proportion':
                statistic_value, ci_lower, ci_upper = \
                    self._calculate_proportion_ci(data_array)
            elif self.statistic_type == 'variance':
                statistic_value, ci_lower, ci_upper = \
                    self._calculate_variance_ci(data_array)
            elif self.statistic_type == 'std':
                statistic_value, ci_lower, ci_upper = \
                    self._calculate_std_ci(data_array)

            # 結果を返す
            result = {
                'tableName': self.table_name,
                'columnName': self.column_name,
                'statistic': {
                    'type': self.statistic_type,
                    'value': statistic_value
                },
                'confidence_interval': {
                    'lower': ci_lower,
                    'upper': ci_upper
                },
                'confidence_level': self.confidence_level
            }
            return result

        except ValidationError:
            # ValidationErrorは再発生させる
            raise
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "confidence interval processing")
            raise ApiError(message) from e

    def _calculate_mean_ci(self, data):
        """平均値の信頼区間を計算"""
        mean_val = np.mean(data)
        sem = stats.sem(data)  # 標準誤差
        n = len(data)
        t_val = stats.t.ppf((1 + self.confidence_level) / 2, df=n-1)
        margin_of_error = t_val * sem

        return \
            float(mean_val), \
            float(mean_val - margin_of_error), \
            float(mean_val + margin_of_error)

    def _calculate_median_ci(self, data):
        """中央値の信頼区間を計算（Bootstrap法）"""
        n = len(data)
        median_val = np.median(data)

        # Bootstrap法で信頼区間を計算
        bootstrap_medians = []
        np.random.seed(42)  # 再現性のため

        for _ in range(1000):
            bootstrap_sample = np.random.choice(data, size=n, replace=True)
            bootstrap_medians.append(np.median(bootstrap_sample))

        alpha = 1 - self.confidence_level
        ci_lower = np.percentile(bootstrap_medians, (alpha/2) * 100)
        ci_upper = np.percentile(bootstrap_medians, (1 - alpha/2) * 100)

        return float(median_val), float(ci_lower), float(ci_upper)

    def _calculate_proportion_ci(self, data):
        """比率の信頼区間を計算（二項分布）"""
        # データを0または1の二項データとして扱う
        unique_vals = np.unique(data)
        if not (len(unique_vals) <= 2 and all(v in [0, 1] for v in unique_vals)):
            raise ValidationError("For proportion confidence interval, data must contain only 0 and 1 values")

        n = len(data)
        successes = np.sum(data)
        proportion = successes / n

        # Wilson score interval（正確な信頼区間）
        z = stats.norm.ppf((1 + self.confidence_level) / 2)
        denominator = 1 + z**2 / n
        center = (proportion + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt((proportion * (1 - proportion) + z**2 / (4 * n)) / n) / denominator

        ci_lower = max(0, center - margin)
        ci_upper = min(1, center + margin)

        return float(proportion), float(ci_lower), float(ci_upper)

    def _calculate_variance_ci(self, data):
        """分散の信頼区間を計算（カイ二乗分布）"""
        n = len(data)
        variance_val = np.var(data, ddof=1)  # 不偏分散

        # カイ二乗分布を使用
        alpha = 1 - self.confidence_level
        chi2_lower = stats.chi2.ppf(alpha/2, df=n-1)
        chi2_upper = stats.chi2.ppf(1-alpha/2, df=n-1)

        ci_lower = (n-1) * variance_val / chi2_upper
        ci_upper = (n-1) * variance_val / chi2_lower

        return float(variance_val), float(ci_lower), float(ci_upper)

    def _calculate_std_ci(self, data):
        """標準偏差の信頼区間を計算"""
        # 分散の信頼区間を求めて平方根を取る
        variance_val, var_ci_lower, var_ci_upper = self._calculate_variance_ci(data)
        std_val = np.sqrt(variance_val)

        ci_lower = np.sqrt(var_ci_lower)
        ci_upper = np.sqrt(var_ci_upper)

        return float(std_val), float(ci_lower), float(ci_upper)


def confidence_interval(table_name: str, column_name: str,
                       confidence_level: float, statistic_type: str) -> Dict:
    """信頼区間計算の関数インターフェース"""
    api = ConfidenceInterval(table_name, column_name, confidence_level, statistic_type)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
        return result
    except ValidationError:
        # Validation errors from execute should also be re-raised
        raise

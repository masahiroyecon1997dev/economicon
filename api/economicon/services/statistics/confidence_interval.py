from typing import ClassVar

import numpy as np
from scipy import stats

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import ConfidenceIntervalRequestBody
from economicon.schemas.enums import ConfidenceIntervalStatisticsType
from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError, ValidationError
from economicon.utils.validators import validate_existence

_RESULT_TYPE = "confidence_interval"


class ConfidenceInterval:
    """
    指定されたテーブルの列の信頼区間を計算するためのAPIクラス

    指定されたテーブルの指定された列に対して、指定された統計の信頼区間を計算します。
    サポートする統計: 平均、中央値、比率、分散、標準偏差
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "column_name": "columnName",
        "confidence_level": "confidenceLevel",
        "statistic_type": "statisticType",
    }

    def __init__(
        self,
        body: ConfidenceIntervalRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ):
        self.tables_store = tables_store
        self.result_store = result_store
        self.table_name = body.table_name
        self.column_name = body.column_name
        self.confidence_level = body.confidence_level
        self.statistic_type = body.statistic_type

    def validate(self):
        # テーブル名の検証
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )

        # 列名の検証
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        validate_existence(
            value=self.column_name,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["column_name"],
        )

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # 列のデータを取得
            column_data = df[self.column_name].drop_nulls()

            # 空データのチェック
            if len(column_data) == 0:
                raise ValidationError(
                    error_code=ErrorCode.CONFIDENCE_INTERVAL_ERROR,
                    message=_("Column contains no valid data"),
                )

            # データを numpy array に変換
            data_array = column_data.to_numpy()

            # 統計量と信頼区間を計算
            match self.statistic_type:
                case ConfidenceIntervalStatisticsType.MEAN:
                    statistic_value, ci_lower, ci_upper = (
                        self._calculate_mean_ci(data_array)
                    )
                case ConfidenceIntervalStatisticsType.MEDIAN:
                    statistic_value, ci_lower, ci_upper = (
                        self._calculate_median_ci(data_array)
                    )
                case ConfidenceIntervalStatisticsType.PROPORTION:
                    statistic_value, ci_lower, ci_upper = (
                        self._calculate_proportion_ci(data_array)
                    )
                case ConfidenceIntervalStatisticsType.VARIANCE:
                    statistic_value, ci_lower, ci_upper = (
                        self._calculate_variance_ci(data_array)
                    )
                case ConfidenceIntervalStatisticsType.STD:
                    statistic_value, ci_lower, ci_upper = (
                        self._calculate_std_ci(data_array)
                    )

            # 結果を返す
            result = {
                "tableName": self.table_name,
                "columnName": self.column_name,
                "statistic": {
                    "type": self.statistic_type.value,
                    "value": statistic_value,
                },
                "confidenceInterval": {"lower": ci_lower, "upper": ci_upper},
                "confidenceLevel": self.confidence_level,
            }

            # AnalysisResultStore に保存
            # （自動命名: "{column} の {stat_type} 信頼区間 #{n}"）
            seq = self.result_store.next_sequence(_RESULT_TYPE)
            name = _("{column} の {stat_type} 信頼区間 #{seq}").format(
                column=self.column_name,
                stat_type=self.statistic_type.value,
                seq=seq,
            )
            analysis_result = AnalysisResult(
                name=name,
                description="",
                table_name=self.table_name,
                result_data=result,
                result_type=_RESULT_TYPE,
            )
            result_id = self.result_store.save_result(analysis_result)
            return {"resultId": result_id}

        except ValidationError:
            # ValidationErrorは再発生させる
            raise
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "confidence interval processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.CONFIDENCE_INTERVAL_ERROR,
                message=message,
                detail=str(e),
            ) from e

    def _calculate_mean_ci(self, data):
        """平均値の信頼区間を計算"""
        mean_val = np.mean(data)
        sem = stats.sem(data)  # 標準誤差
        n = len(data)
        t_val = stats.t.ppf((1 + self.confidence_level) / 2, df=n - 1)
        margin_of_error = t_val * sem

        return (
            float(mean_val),
            float(mean_val - margin_of_error),
            float(mean_val + margin_of_error),
        )

    def _calculate_median_ci(self, data):
        """中央値の信頼区間を計算（Bootstrap法）"""
        n = len(data)
        median_val = np.median(data)

        # Bootstrap法で信頼区間を計算
        bootstrap_medians = []
        rng = np.random.default_rng()

        for _index in range(1000):
            bootstrap_sample = rng.choice(data, size=n, replace=True)
            bootstrap_medians.append(np.median(bootstrap_sample))

        alpha = 1 - self.confidence_level
        ci_lower = np.percentile(bootstrap_medians, (alpha / 2) * 100)
        ci_upper = np.percentile(bootstrap_medians, (1 - alpha / 2) * 100)

        return float(median_val), float(ci_lower), float(ci_upper)

    def _calculate_proportion_ci(self, data):
        """比率の信頼区間を計算（二項分布）"""
        # データを0または1の二項データとして扱う
        unique_vals = np.unique(data)
        supremum = 2
        if not (
            len(unique_vals) <= supremum
            and all(v in [0, 1] for v in unique_vals)
        ):
            raise ValidationError(
                error_code=ErrorCode.INVALID_PROPORTION_DATA,
                message=_(
                    "For proportion confidence interval, "
                    "data must contain only 0 and 1 values"
                ),
            )

        n = len(data)
        successes = np.sum(data)
        proportion = successes / n

        # Wilson score interval（正確な信頼区間）
        z = stats.norm.ppf((1 + self.confidence_level) / 2)
        denominator = 1 + z**2 / n
        center = (proportion + z**2 / (2 * n)) / denominator
        margin = (
            z
            * np.sqrt((proportion * (1 - proportion) + z**2 / (4 * n)) / n)
            / denominator
        )

        ci_lower = max(0, center - margin)
        ci_upper = min(1, center + margin)

        return float(proportion), float(ci_lower), float(ci_upper)

    def _calculate_variance_ci(self, data):
        """分散の信頼区間を計算（カイ二乗分布）"""
        n = len(data)
        variance_val = np.var(data, ddof=1)  # 不偏分散

        # カイ二乗分布を使用
        alpha = 1 - self.confidence_level
        chi2_lower = stats.chi2.ppf(alpha / 2, df=n - 1)
        chi2_upper = stats.chi2.ppf(1 - alpha / 2, df=n - 1)

        ci_lower = (n - 1) * variance_val / chi2_upper
        ci_upper = (n - 1) * variance_val / chi2_lower

        return float(variance_val), float(ci_lower), float(ci_upper)

    def _calculate_std_ci(self, data):
        """標準偏差の信頼区間を計算"""
        # 分散の信頼区間を求めて平方根を取る
        variance_val, var_ci_lower, var_ci_upper = self._calculate_variance_ci(
            data
        )
        std_val = np.sqrt(variance_val)

        ci_lower = np.sqrt(var_ci_lower)
        ci_upper = np.sqrt(var_ci_upper)

        return float(std_val), float(ci_lower), float(ci_upper)

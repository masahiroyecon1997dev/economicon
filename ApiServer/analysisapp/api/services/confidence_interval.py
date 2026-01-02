from typing import Dict

import numpy as np
from .django_compat import gettext as _
from scipy import stats

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import (ValidationError,
                                                     validate_candidates)
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name)
from .abstract_api import AbstractApi, ApiError


class ConfidenceInterval(AbstractApi):
    """
    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ蛻励・菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ励☆繧九◆繧√・API繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ謖・ｮ壹＆繧後◆蛻励↓蟇ｾ縺励※縲∵欠螳壹＆繧後◆邨ｱ險医・菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ励＠縺ｾ縺吶・    繧ｵ繝昴・繝医☆繧狗ｵｱ險・ 蟷ｳ蝮・∽ｸｭ螟ｮ蛟､縲∵ｯ皮紫縲∝・謨｣縲∵ｨ呎ｺ門￥蟾ｮ
    """

    # 蛻ｩ逕ｨ蜿ｯ閭ｽ縺ｪ邨ｱ險医・遞ｮ鬘槭ｒ螳夂ｾｩ
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
            # 繝・・繝悶Ν蜷阪・讀懆ｨｼ
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 蛻怜錐縺ｮ讀懆ｨｼ
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_existed_column_name(
                self.column_name,
                column_name_list,
                self.param_names['column_name']
            )

            # 邨ｱ險医ち繧､繝励・讀懆ｨｼ
            validate_candidates(
                self.statistic_type,
                self.param_names['statistic_type'],
                list(self.AVAILABLE_STATISTICS.keys())
            )

            # 菫｡鬆ｼ蠎ｦ繝ｬ繝吶Ν縺ｮ讀懆ｨｼ
            if not isinstance(self.confidence_level, (int, float)):
                raise ValidationError("confidenceLevel must be a number")

            if not (0 < self.confidence_level < 1):
                raise ValidationError("confidenceLevel must be "
                                      "between 0 and 1")

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # 蛻励・繝・・繧ｿ繧貞叙蠕・            column_data = df[self.column_name].drop_nulls()

            if column_data.len() == 0:
                raise ValidationError("Column contains no valid data")

            # 繝・・繧ｿ繧・numpy array 縺ｫ螟画鋤
            data_array = column_data.to_numpy()

            # 邨ｱ險磯㍼縺ｨ菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ・            match self.statistic_type:
                case 'mean':
                    statistic_value, ci_lower, ci_upper = \
                        self._calculate_mean_ci(data_array)
                case 'median':
                    statistic_value, ci_lower, ci_upper = \
                        self._calculate_median_ci(data_array)
                case 'proportion':
                    statistic_value, ci_lower, ci_upper = \
                        self._calculate_proportion_ci(data_array)
                case 'variance':
                    statistic_value, ci_lower, ci_upper = \
                        self._calculate_variance_ci(data_array)
                case 'std':
                    statistic_value, ci_lower, ci_upper = \
                        self._calculate_std_ci(data_array)
                case _:
                    raise ValidationError("Unsupported statistic type")

            # 邨先棡繧定ｿ斐☆
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
            # ValidationError縺ｯ蜀咲匱逕溘＆縺帙ｋ
            raise
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "confidence interval processing")
            raise ApiError(message) from e

    def _calculate_mean_ci(self, data):
        """蟷ｳ蝮・､縺ｮ菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ・""
        mean_val = np.mean(data)
        sem = stats.sem(data)  # 讓呎ｺ冶ｪ､蟾ｮ
        n = len(data)
        t_val = stats.t.ppf((1 + self.confidence_level) / 2, df=n-1)
        margin_of_error = t_val * sem

        return \
            float(mean_val), \
            float(mean_val - margin_of_error), \
            float(mean_val + margin_of_error)

    def _calculate_median_ci(self, data):
        """荳ｭ螟ｮ蛟､縺ｮ菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ暦ｼ・ootstrap豕包ｼ・""
        n = len(data)
        median_val = np.median(data)

        # Bootstrap豕輔〒菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ・        bootstrap_medians = []
        np.random.seed(42)  # 蜀咲樟諤ｧ縺ｮ縺溘ａ

        for _index in range(1000):
            bootstrap_sample = np.random.choice(data, size=n, replace=True)
            bootstrap_medians.append(np.median(bootstrap_sample))

        alpha = 1 - self.confidence_level
        ci_lower = np.percentile(bootstrap_medians, (alpha/2) * 100)
        ci_upper = np.percentile(bootstrap_medians, (1 - alpha/2) * 100)

        return float(median_val), float(ci_lower), float(ci_upper)

    def _calculate_proportion_ci(self, data):
        """豈皮紫縺ｮ菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ暦ｼ井ｺ碁・・蟶・ｼ・""
        # 繝・・繧ｿ繧・縺ｾ縺溘・1縺ｮ莠碁・ョ繝ｼ繧ｿ縺ｨ縺励※謇ｱ縺・        unique_vals = np.unique(data)
        if not (
            len(unique_vals) <= 2 and all(v in [0, 1] for v in unique_vals)
        ):
            raise ValidationError("For proportion confidence interval, "
                                  "data must contain only 0 and 1 values")

        n = len(data)
        successes = np.sum(data)
        proportion = successes / n

        # Wilson score interval・域ｭ｣遒ｺ縺ｪ菫｡鬆ｼ蛹ｺ髢難ｼ・        z = stats.norm.ppf((1 + self.confidence_level) / 2)
        denominator = 1 + z**2 / n
        center = (proportion + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt(
            (proportion * (1 - proportion) + z**2 / (4 * n)) / n
        ) / denominator

        ci_lower = max(0, center - margin)
        ci_upper = min(1, center + margin)

        return float(proportion), float(ci_lower), float(ci_upper)

    def _calculate_variance_ci(self, data):
        """蛻・淵縺ｮ菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ暦ｼ医き繧､莠御ｹ怜・蟶・ｼ・""
        n = len(data)
        variance_val = np.var(data, ddof=1)  # 荳榊￥蛻・淵

        # 繧ｫ繧､莠御ｹ怜・蟶・ｒ菴ｿ逕ｨ
        alpha = 1 - self.confidence_level
        chi2_lower = stats.chi2.ppf(alpha/2, df=n-1)
        chi2_upper = stats.chi2.ppf(1-alpha/2, df=n-1)

        ci_lower = (n-1) * variance_val / chi2_upper
        ci_upper = (n-1) * variance_val / chi2_lower

        return float(variance_val), float(ci_lower), float(ci_upper)

    def _calculate_std_ci(self, data):
        """讓呎ｺ門￥蟾ｮ縺ｮ菫｡鬆ｼ蛹ｺ髢薙ｒ險育ｮ・""
        # 蛻・淵縺ｮ菫｡鬆ｼ蛹ｺ髢薙ｒ豎ゅａ縺ｦ蟷ｳ譁ｹ譬ｹ繧貞叙繧・        variance_val, var_ci_lower, var_ci_upper = self._calculate_variance_ci(
            data
        )
        std_val = np.sqrt(variance_val)

        ci_lower = np.sqrt(var_ci_lower)
        ci_upper = np.sqrt(var_ci_upper)

        return float(std_val), float(ci_lower), float(ci_upper)


def confidence_interval(table_name: str, column_name: str,
                        confidence_level: float, statistic_type: str) -> Dict:
    """菫｡鬆ｼ蛹ｺ髢楢ｨ育ｮ励・髢｢謨ｰ繧､繝ｳ繧ｿ繝ｼ繝輔ぉ繝ｼ繧ｹ"""
    api = ConfidenceInterval(table_name,
                             column_name,
                             confidence_level,
                             statistic_type)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
        return result
    except ValidationError:
        # Validation errors from execute should also be re-raised
        raise

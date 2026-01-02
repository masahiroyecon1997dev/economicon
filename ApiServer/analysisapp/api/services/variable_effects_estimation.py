from typing import Dict, List, Literal

import statsmodels.api as sm
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.statistics_validators import (
    validate_dependent_variable, validate_explanatory_variables)
from ..utils.validator.tables_manager_validator import \
    validate_existed_table_name
from .abstract_api import AbstractApi, ApiError

CovType = Literal['nonrobust', 'fixed scale', 'HC0', 'HC1', 'HC2',
                  'HC3', 'HAC', 'hac-panel', 'hac-groupsum',
                  'cluster']


class VariableEffectsEstimation(AbstractApi):
    """
    螟蛾㍼蜉ｹ譫懈耳螳壼・譫舌ｒ陦後≧縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ蛻励ｒ菴ｿ逕ｨ縺励※蝗槫ｸｰ蛻・梵繧貞ｮ溯｡後＠縲・    逡ｰ縺ｪ繧区ｨ呎ｺ冶ｪ､蟾ｮ險育ｮ玲婿豕輔ｒ驕ｩ逕ｨ縺ｧ縺阪∪縺吶・    """

    # 繧ｵ繝昴・繝医☆繧区ｨ呎ｺ冶ｪ､蟾ｮ險育ｮ玲婿豕・    SUPPORTED_STANDARD_ERROR_METHODS = [
        'nonrobust',     # 騾壼ｸｸ縺ｮ險育ｮ玲婿豕・        'HC0',           # White's heteroskedasticity-consistent
        'HC1',           # HC0 with degrees of freedom correction
        'HC2',           # HC0 with leverage correction
        'HC3',           # HC0 with more robust leverage correction
        'HAC',           # Heteroskedasticity and autocorrelation consistent
        'hac-panel',     # 繝代ロ繝ｫ繝・・繧ｿ逕ｨ縺ｮHAC
        'hac-groupsum',  # 繧ｰ繝ｫ繝ｼ繝鈴寔邏・畑縺ｮHAC
        'cluster'        # 繧ｯ繝ｩ繧ｹ繧ｿ繝ｪ繝ｳ繧ｰ逕ｨ
    ]

    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        standard_error_method: str = 'nonrobust',
        use_t_distribution: bool = True
    ):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.dependent_variable = dependent_variable
        self.explanatory_variables = explanatory_variables
        self.standard_error_method = standard_error_method
        self.use_t_distribution = use_t_distribution
        self.param_names = {
            'table_name': 'tableName',
            'dependent_variable': 'dependentVariable',
            'explanatory_variables': 'explanatoryVariables',
            'standard_error_method': 'standardErrorMethod',
            'use_t_distribution': 'useTDistribution'
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

            # 蛻怜錐繝ｪ繧ｹ繝医・蜿門ｾ・            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)

            # 隱ｬ譏主､画焚縺ｮ讀懆ｨｼ
            df_schema = self.tables_manager.get_column_info_list(
                self.table_name)
            validate_explanatory_variables(
                self.explanatory_variables,
                column_name_list,
                df_schema,
                self.param_names['explanatory_variables']
            )

            # 陲ｫ隱ｬ譏主､画焚縺ｮ讀懆ｨｼ
            validate_dependent_variable(
                self.dependent_variable,
                column_name_list,
                self.explanatory_variables,
                df_schema,
                self.param_names['dependent_variable']
            )

            # 讓呎ｺ冶ｪ､蟾ｮ險育ｮ玲婿豕輔・讀懆ｨｼ
            if (self.standard_error_method not
                    in self.SUPPORTED_STANDARD_ERROR_METHODS):
                message = _(f"{self.param_names['standard_error_method']} "
                            "must be one of: "
                            f"{', '.join(
                                self.SUPPORTED_STANDARD_ERROR_METHODS)}")
                raise ValidationError(message)

            return None
        except ValidationError as e:
            return e

    def execute(self) -> Dict:
        try:
            # 繝・・繝悶Ν縺ｮ蜿門ｾ・            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # 繝・・繧ｿ縺ｮ貅門ｙ
            # 陲ｫ隱ｬ譏主､画焚縺ｮ繝・・繧ｿ繧貞叙蠕・            y_data = df[self.dependent_variable].to_numpy()

            # 隱ｬ譏主､画焚縺ｮ繝・・繧ｿ繧貞叙蠕・            x_data = df.select(self.explanatory_variables).to_numpy()

            # 螳壽焚鬆・ｒ霑ｽ蜉
            x_data_with_const = sm.add_constant(x_data)

            # OLS繝｢繝・Ν繧剃ｽ懈・縺励∵欠螳壹＆繧後◆讓呎ｺ冶ｪ､蟾ｮ譁ｹ豕輔〒繝輔ぅ繝・ヨ
            model = sm.OLS(y_data, x_data_with_const)

            # 讓呎ｺ冶ｪ､蟾ｮ譁ｹ豕輔↓蠢懊§縺ｦcov_kwds繧定ｨｭ螳・            cov_kwds = None
            cov_type: CovType = 'nonrobust'
            match (self.standard_error_method):
                case 'nonrobust':
                    cov_type = 'nonrobust'
                case 'fixed scale':
                    cov_type = 'fixed scale'
                case 'HC0':
                    cov_type = 'HC0'
                case 'HC1':
                    cov_type = 'HC1'
                case 'HC2':
                    cov_type = 'HC2'
                case 'HC3':
                    cov_type = 'HC3'
                case 'HAC':
                    cov_type = 'HAC'
                    cov_kwds = {'maxlags': 1}
                case 'hac-panel':
                    cov_type = 'hac-panel'
                case 'hac-groupsum':
                    cov_type = 'hac-groupsum'
                case 'cluster':
                    cov_type = 'cluster'

            results = model.fit(
                cov_type=cov_type,
                cov_kwds=cov_kwds,
                use_t=self.use_t_distribution
            )

            # 邨先棡縺ｮ謨ｴ逅・            summary_text = results.summary().as_text()

            # 繝代Λ繝｡繝ｼ繧ｿ縺ｮ隧ｳ邏ｰ諠・ｱ
            param_names = ['const'] + self.explanatory_variables
            params_info = []
            for i, name in enumerate(param_names):
                # 菫｡鬆ｼ蛹ｺ髢薙ｒ蜿門ｾ・                conf_int = results.conf_int()
                params_info.append({
                    'variable': name,
                    'coefficient': float(results.params[i]),
                    'standardError': float(results.bse[i]),
                    'pValue': float(results.pvalues[i]),
                    'tValue':
                        float(results.tvalues[i])
                        if self.use_t_distribution else float(
                            results.tvalues[i]),
                    'confidenceIntervalLower': float(conf_int[i, 0]),
                    'confidenceIntervalUpper': float(conf_int[i, 1])
                })

            # 繝｢繝・Ν邨ｱ險域ュ蝣ｱ
            model_stats = {
                'R2': float(results.rsquared),
                'adjustedR2': float(results.rsquared_adj),
                'AIC': float(results.aic),
                'BIC': float(results.bic),
                'fValue': float(results.fvalue),
                'fProbability': float(results.f_pvalue),
                'logLikelihood': float(results.llf),
                'nObservations': int(results.nobs),
                'degreesOfFreedom': int(results.df_model),
                'residualDegreesOfFreedom': int(results.df_resid)
            }

            # 邨先棡繧定ｿ斐☆
            result = {
                'tableName': self.table_name,
                'dependentVariable': self.dependent_variable,
                'explanatoryVariables': self.explanatory_variables,
                'standardErrorMethod': self.standard_error_method,
                'useTDistribution': self.use_t_distribution,
                'regressionResult': summary_text,
                'parameters': params_info,
                'modelStatistics': model_stats
            }
            return result

        except Exception as e:
            message = _("An unexpected error occurred during "
                        "variable effects estimation processing")
            raise ApiError(message) from e


def variable_effects_estimation(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    standard_error_method: str = 'nonrobust',
    use_t_distribution: bool = True
) -> Dict:
    """
    螟蛾㍼蜉ｹ譫懈耳螳壼・譫舌ｒ螳溯｡後☆繧矩未謨ｰ

    Args:
        table_name: 繝・・繝悶Ν蜷・        dependent_variable: 陲ｫ隱ｬ譏主､画焚縺ｮ蛻怜錐
        explanatory_variables: 隱ｬ譏主､画焚縺ｮ蛻怜錐繝ｪ繧ｹ繝・        standard_error_method: 讓呎ｺ冶ｪ､蟾ｮ縺ｮ險育ｮ玲婿豕・        use_t_distribution: t蛻・ｸ・ｒ菴ｿ逕ｨ縺吶ｋ縺九←縺・°

    Returns:
        蛻・梵邨先棡繧貞性繧霎樊嶌
    """
    api = VariableEffectsEstimation(
        table_name,
        dependent_variable,
        explanatory_variables,
        standard_error_method,
        use_t_distribution
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

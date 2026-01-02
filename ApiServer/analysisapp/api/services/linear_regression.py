import statsmodels.api as sm
from .django_compat import gettext as _
from typing import Dict, List
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name
)
from ..utils.validator.statistics_validators import (
    validate_dependent_variable,
    validate_explanatory_variables
)
from .data.tables_manager import TablesManager
from .abstract_api import AbstractApi, ApiError


class LinearRegression(AbstractApi):
    """
    邱壼ｽ｢蝗槫ｸｰ蛻・梵繧定｡後≧縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ蛻励ｒ菴ｿ逕ｨ縺励※邱壼ｽ｢蝗槫ｸｰ蛻・梵繧貞ｮ溯｡後＠縺ｾ縺吶・    陲ｫ隱ｬ譏主､画焚・亥ｾ灘ｱ槫､画焚・・蛻励→隱ｬ譏主､画焚・育峡遶句､画焚・芽､・焚蛻励ｒ謖・ｮ壹＠縺ｾ縺吶・    """
    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str]
    ):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.dependent_variable = dependent_variable
        self.explanatory_variables = explanatory_variables
        self.param_names = {
            'table_name': 'tableName',
            'dependent_variable': 'dependentVariable',
            'explanatory_variables': 'explanatoryVariables'
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

            # 邱壼ｽ｢蝗槫ｸｰ繝｢繝・Ν縺ｮ螳溯｡・            model = sm.OLS(y_data, x_data_with_const).fit()

            # 邨先棡縺ｮ謨ｴ逅・            summary_text = model.summary().as_text()

            # 繝代Λ繝｡繝ｼ繧ｿ縺ｮ隧ｳ邏ｰ諠・ｱ
            param_names = ['const'] + self.explanatory_variables
            params_info = []
            for i, name in enumerate(param_names):
                params_info.append({
                    'variable': name,
                    'coefficient': float(model.params[i]),
                    'standardError': float(model.bse[i]),
                    'pValue': float(model.pvalues[i]),
                    'tValue': float(model.tvalues[i])
                })

            # 繝｢繝・Ν邨ｱ險域ュ蝣ｱ
            model_stats = {
                'R2': float(model.rsquared),
                'adjustedR2': float(model.rsquared_adj),
                'AIC': float(model.aic),
                'BIC': float(model.bic),
                'fValue': float(model.fvalue),
                'fProbability': float(model.f_pvalue),
                'logLikelihood': float(model.llf),
                'nObservations': int(model.nobs)
            }

            # 邨先棡繧定ｿ斐☆
            result = {
                'tableName': self.table_name,
                'dependentVariable': self.dependent_variable,
                'explanatoryVariables': self.explanatory_variables,
                'regressionResult': summary_text,
                'parameters': params_info,
                'modelStatistics': model_stats
            }
            return result

        except Exception as e:
            message = _("An unexpected error occurred during "
                        "linear regression processing")
            raise ApiError(message) from e


def linear_regression(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str]
) -> Dict:
    """
    邱壼ｽ｢蝗槫ｸｰ蛻・梵繧貞ｮ溯｡後☆繧矩未謨ｰ

    Args:
        table_name: 繝・・繝悶Ν蜷・        dependent_variable: 陲ｫ隱ｬ譏主､画焚縺ｮ蛻怜錐
        explanatory_variables: 隱ｬ譏主､画焚縺ｮ蛻怜錐繝ｪ繧ｹ繝・
    Returns:
        蛻・梵邨先棡繧貞性繧霎樊嶌
    """
    api = LinearRegression(table_name,
                           dependent_variable,
                           explanatory_variables)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

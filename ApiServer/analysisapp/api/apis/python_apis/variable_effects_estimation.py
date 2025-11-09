from typing import Dict, List, Literal

import statsmodels.api as sm
from django.utils.translation import gettext as _

from ..data.tables_manager import TablesManager
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.statistics_validators import (
    validate_dependent_variable, validate_explanatory_variables)
from ..utilities.validator.tables_manager_validator import \
    validate_existed_table_name
from .common_api_class import AbstractApi, ApiError

CovType = Literal['nonrobust', 'fixed scale', 'HC0', 'HC1', 'HC2',
                  'HC3', 'HAC', 'hac-panel', 'hac-groupsum',
                  'cluster']


class VariableEffectsEstimation(AbstractApi):
    """
    変量効果推定分析を行うためのAPIクラス

    指定されたテーブルの列を使用して回帰分析を実行し、
    異なる標準誤差計算方法を適用できます。
    """

    # サポートする標準誤差計算方法
    SUPPORTED_STANDARD_ERROR_METHODS = [
        'nonrobust',     # 通常の計算方法
        'HC0',           # White's heteroskedasticity-consistent
        'HC1',           # HC0 with degrees of freedom correction
        'HC2',           # HC0 with leverage correction
        'HC3',           # HC0 with more robust leverage correction
        'HAC',           # Heteroskedasticity and autocorrelation consistent
        'hac-panel',     # パネルデータ用のHAC
        'hac-groupsum',  # グループ集約用のHAC
        'cluster'        # クラスタリング用
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
            # テーブル名の検証
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 列名リストの取得
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)

            # 説明変数の検証
            df_schema = self.tables_manager.get_column_info_list(
                self.table_name)
            validate_explanatory_variables(
                self.explanatory_variables,
                column_name_list,
                df_schema,
                self.param_names['explanatory_variables']
            )

            # 被説明変数の検証
            validate_dependent_variable(
                self.dependent_variable,
                column_name_list,
                self.explanatory_variables,
                df_schema,
                self.param_names['dependent_variable']
            )

            # 標準誤差計算方法の検証
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
            # テーブルの取得
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # データの準備
            # 被説明変数のデータを取得
            y_data = df[self.dependent_variable].to_numpy()

            # 説明変数のデータを取得
            x_data = df.select(self.explanatory_variables).to_numpy()

            # 定数項を追加
            x_data_with_const = sm.add_constant(x_data)

            # OLSモデルを作成し、指定された標準誤差方法でフィット
            model = sm.OLS(y_data, x_data_with_const)

            # 標準誤差方法に応じてcov_kwdsを設定
            cov_kwds = None
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

            # 結果の整理
            summary_text = results.summary().as_text()

            # パラメータの詳細情報
            param_names = ['const'] + self.explanatory_variables
            params_info = []
            for i, name in enumerate(param_names):
                # 信頼区間を取得
                conf_int = results.conf_int()
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

            # モデル統計情報
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

            # 結果を返す
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
    変量効果推定分析を実行する関数

    Args:
        table_name: テーブル名
        dependent_variable: 被説明変数の列名
        explanatory_variables: 説明変数の列名リスト
        standard_error_method: 標準誤差の計算方法
        use_t_distribution: t分布を使用するかどうか

    Returns:
        分析結果を含む辞書
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

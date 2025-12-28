import statsmodels.api as sm
from django.utils.translation import gettext as _
from typing import Dict, List
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator import (
    validate_existed_table_name
)
from ..utilities.validator.statistics_validators import (
    validate_dependent_variable,
    validate_explanatory_variables
)
from ..data.tables_manager import TablesManager
from .abstract_api import (AbstractApi, ApiError)


class LogisticRegression(AbstractApi):
    """
    ロジット分析を行うためのAPIクラス

    指定されたテーブルの列を使用してロジスティック回帰分析を実行します。
    被説明変数（従属変数）1列と説明変数（独立変数）複数列を指定します。
    """
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

            return None
        except ValidationError as e:
            return e

    def execute(self):
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

            # ロジスティック回帰の実行
            model = sm.Logit(y_data, x_data_with_const).fit()

            # 結果の整理
            summary_text = model.summary().as_text()

            # パラメータの詳細情報
            param_names = ['const'] + self.explanatory_variables
            params_info = []
            for i, name in enumerate(param_names):
                params_info.append({
                    'variable': name,
                    'coefficient': float(model.params[i]),
                    'pValue': float(model.pvalues[i]),
                    'tValue': float(model.tvalues[i])
                })

            # モデル統計情報
            model_stats = {
                'AIC': float(model.aic),
                'BIC': float(model.bic),
                'logLikelihood': float(model.llf),
                'pseudoRSquared': float(model.prsquared),
                'nObservations': int(model.nobs)
            }

            # 結果を返す
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
                        "logistic regression processing")
            raise ApiError(message) from e


def logistic_regression(table_name: str,
                        dependent_variable: str,
                        explanatory_variables: List[str]) -> Dict:
    """
    ロジット分析を実行する関数

    Args:
        table_name: テーブル名
        dependent_variable: 被説明変数の列名
        explanatory_variables: 説明変数の列名リスト

    Returns:
        分析結果を含む辞書
    """
    api = LogisticRegression(table_name, dependent_variable,
                             explanatory_variables)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

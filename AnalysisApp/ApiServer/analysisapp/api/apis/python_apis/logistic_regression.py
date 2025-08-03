import polars as pl
import statsmodels.api as sm
import numpy as np
from django.utils.translation import gettext as _
from typing import Dict, List
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import InputValidator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class LogisticRegression(AbstractApi):
    """
    ロジット分析を行うためのAPIクラス

    指定されたテーブルの列を使用してロジスティック回帰分析を実行します。
    被説明変数（従属変数）1列と説明変数（独立変数）複数列を指定します。
    """
    def __init__(self, table_name: str, dependent_variable: str,
                 explanatory_variables: List[str]):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.dependent_variable = dependent_variable
        self.explanatory_variables = explanatory_variables
        self.param_names = {
                'table_name': 'tableName',
                'column_names': 'dependentVariable',
            }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            
            # テーブル名の検証
            table_name_list = self.tables_manager.get_table_name_list()
            validator.validate_existed_table_name(self.table_name,
                                                  table_name_list)
            
            # 列名リストの取得
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            
            # 被説明変数の検証
            validator.validate_existed_column_name(self.dependent_variable,
                                                   column_name_list)
            
            # 説明変数の検証
            if not self.explanatory_variables:
                raise ValidationError(_("At least one explanatory variable is required"))
            
            # 各説明変数が存在するかチェック
            for var in self.explanatory_variables:
                if var not in column_name_list:
                    raise ValidationError(_("explanatoryVariables '{}' does not exist.").format(var))
            
            # 被説明変数が説明変数に含まれていないかチェック
            if self.dependent_variable in self.explanatory_variables:
                raise ValidationError(_("Dependent variable cannot be included in explanatory variables"))
            
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
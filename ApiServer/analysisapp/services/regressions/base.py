"""
回帰分析サービスの抽象基底クラス

全ての回帰分析サービスが継承する共通インターフェースを定義します。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Literal, Union
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper

from ..data.tables_store import TablesStore
from ...utils.validator.common_validators import ValidationError
from ...utils.validator.tables_store_validator import (
    validate_existed_table_name
)
from ...utils.validator.statistics_validators import (
    validate_dependent_variable,
    validate_explanatory_variables
)
from ..abstract_api import AbstractApi, ApiError
from ..django_compat import gettext as _

# 型エイリアス
StandardErrorMethod = Literal[
    'nonrobust', 'hc0', 'hc1', 'hc2', 'hc3', 'hac', 'clustered'
]
MissingValueHandling = Literal['ignore', 'remove', 'error']


class AbstractRegressionService(AbstractApi, ABC):
    """
    回帰分析サービスの抽象基底クラス

    全ての回帰分析クラスはこのクラスを継承し、fit() メソッドを実装します。
    """

    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        standard_error_method: str = 'nonrobust',
        standard_error_params: Optional[Dict[str, Any]] = None,
        use_t_distribution: bool = True,
        has_const: bool = True,
        missing_value_handling: MissingValueHandling = 'remove'
    ):
        """
        初期化

        Args:
            table_name: テーブル名
            dependent_variable: 被説明変数の列名
            explanatory_variables: 説明変数の列名リスト
            standard_error_method: 標準誤差計算方法
            standard_error_params: 標準誤差計算のパラメータ
            use_t_distribution: t分布を使用するか
            has_const: 定数項を追加するか
            missing_value_handling: 欠損値の処理方法
        """
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.dependent_variable = dependent_variable
        self.explanatory_variables = explanatory_variables
        self.standard_error_method = standard_error_method
        self.standard_error_params = standard_error_params or {}
        self.use_t_distribution = use_t_distribution
        self.has_const = has_const
        self.missing_value_handling = missing_value_handling

        self.param_names = {
            'table_name': 'tableName',
            'dependent_variable': 'dependentVariable',
            'explanatory_variables': 'explanatoryVariables',
            'standard_error_method': 'standardErrorMethod',
            'standard_error_params': 'standardErrorParams',
            'use_t_distribution': 'useTDistribution',
            'has_const': 'hasConst',
            'missing_value_handling': 'missingValueHandling'
        }

    def validate(self) -> Optional[ValidationError]:
        """
        共通のバリデーション処理

        Returns:
            ValidationError: バリデーションエラー、問題なければNone
        """
        try:
            # テーブル名の検証
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 列名リストの取得
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )

            # スキーマの取得
            df_schema = self.tables_store.get_column_info_list(
                self.table_name
            )

            # 説明変数の検証
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

            # 標準誤差方法の検証
            if self.standard_error_method == 'clustered':
                if 'groups' not in self.standard_error_params:
                    message = _(
                        "standardErrorParams requires 'groups' "
                        "(cluster variable name)"
                    )
                    raise ValidationError(message)

                # クラスタ変数が存在するか確認
                groups_col = self.standard_error_params['groups']
                if groups_col not in column_name_list:
                    message = _("{} is not an existing column name").format(
                        groups_col
                    )
                    raise ValidationError(message)

            # サブクラス固有のバリデーション
            self._validate_specific()

            return None
        except ValidationError as e:
            return e

    @abstractmethod
    def _validate_specific(self):
        """
        サブクラス固有のバリデーション処理

        サブクラスで必要に応じてオーバーライドします。
        """
        pass

    def execute(self) -> Dict:
        """
        回帰分析の実行

        Returns:
            分析結果を含む辞書
        """
        try:
            # テーブルの取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # データの準備
            y_data = df[self.dependent_variable].to_numpy()
            x_data = df.select(self.explanatory_variables).to_numpy()

            # 定数項の追加
            if self.has_const:
                x_data = sm.add_constant(x_data)

            # 欠損値の処理を statsmodels の形式に変換
            missing_handling_map = {
                'ignore': 'none',
                'remove': 'drop',
                'error': 'raise'
            }
            missing = missing_handling_map.get(
                self.missing_value_handling, 'drop'
            )

            # モデルのフィット
            model_result = self.fit(y_data, x_data, missing)

            # 結果の整理
            result = self._format_result(model_result)

            return result

        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "regression analysis execution"
            )
            raise ApiError(message) from e

    @abstractmethod
    def fit(
        self,
        y_data,
        x_data,
        missing: str
    ) -> Any:
        """
        回帰モデルのフィッティング

        サブクラスで実装する必要があります。

        Args:
            y_data: 被説明変数のデータ
            x_data: 説明変数のデータ
            missing: 欠損値の処理方法 ('none', 'drop', 'raise')

        Returns:
            回帰結果オブジェクト
        """
        pass

    def _format_result(
        self,
        model_result: Any
    ) -> Dict:
        """
        分析結果を JSON 形式にフォーマット

        Args:
            model_result: statsmodels の回帰結果オブジェクト

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = model_result.summary().as_text()

        # パラメータの詳細情報
        param_names = (
            ['const'] if self.has_const else []
        ) + self.explanatory_variables
        params_info = []

        for i, name in enumerate(param_names):
            param_dict = {
                'variable': name,
                'coefficient': float(model_result.params[i]),
                'standardError': float(model_result.bse[i]),
                'pValue': float(model_result.pvalues[i]),
            }

            # t値またはz値
            if hasattr(model_result, 'tvalues'):
                param_dict['tValue'] = float(model_result.tvalues[i])

            # 信頼区間
            if hasattr(model_result, 'conf_int'):
                conf_int = model_result.conf_int()
                param_dict['confidenceIntervalLower'] = float(
                    conf_int[i, 0]
                )
                param_dict['confidenceIntervalUpper'] = float(
                    conf_int[i, 1]
                )

            params_info.append(param_dict)

        # モデル統計情報
        model_stats: Dict[str, Any] = {
            'nObservations': int(model_result.nobs)
        }

        # 線形モデルの統計量
        if hasattr(model_result, 'rsquared'):
            model_stats['R2'] = float(model_result.rsquared)
        if hasattr(model_result, 'rsquared_adj'):
            model_stats['adjustedR2'] = float(model_result.rsquared_adj)
        if hasattr(model_result, 'fvalue'):
            model_stats['fValue'] = float(model_result.fvalue)
        if hasattr(model_result, 'f_pvalue'):
            model_stats['fProbability'] = float(model_result.f_pvalue)

        # 共通の統計量
        if hasattr(model_result, 'aic'):
            model_stats['AIC'] = float(model_result.aic)
        if hasattr(model_result, 'bic'):
            model_stats['BIC'] = float(model_result.bic)
        if hasattr(model_result, 'llf'):
            model_stats['logLikelihood'] = float(model_result.llf)

        # 離散選択モデルの統計量
        if hasattr(model_result, 'prsquared'):
            model_stats['pseudoRSquared'] = float(model_result.prsquared)

        result = {
            'tableName': self.table_name,
            'dependentVariable': self.dependent_variable,
            'explanatoryVariables': self.explanatory_variables,
            'regressionResult': summary_text,
            'parameters': params_info,
            'modelStatistics': model_stats
        }

        return result

    def _apply_standard_errors(
        self,
        model_result: Any
    ) -> Any:
        """
        標準誤差の計算方法を適用

        Args:
            model_result: 初期の回帰結果

        Returns:
            標準誤差が調整された回帰結果
        """
        if self.standard_error_method == 'nonrobust':
            return model_result

        cov_type_map = {
            'hc0': 'HC0',
            'hc1': 'HC1',
            'hc2': 'HC2',
            'hc3': 'HC3',
            'hac': 'HAC',
            'clustered': 'cluster'
        }

        cov_type = cov_type_map.get(self.standard_error_method)
        if not cov_type:
            return model_result

        # HACの場合はmaxlagsを渡す (デフォルトは sqrt(n) に基づく計算)
        if self.standard_error_method == 'hac':
            maxlags = self.standard_error_params.get('maxlags')
            if maxlags is None:
                # maxlagsが未指定の場合、デフォルト値を計算
                import numpy as np
                table_info = self.tables_store.get_table(self.table_name)
                n = len(table_info.table)
                maxlags = int(np.floor(4 * (n / 100) ** (2 / 9)))
            return model_result.get_robustcov_results(
                cov_type=cov_type,
                maxlags=maxlags
            )

        # クラスタリングの場合は groups を渡す
        if self.standard_error_method == 'clustered':
            groups_col = self.standard_error_params.get('groups')
            if groups_col:
                table_info = self.tables_store.get_table(self.table_name)
                df = table_info.table
                groups = df[groups_col].to_numpy()
                return model_result.get_robustcov_results(
                    cov_type=cov_type,
                    groups=groups
                )

        return model_result.get_robustcov_results(cov_type=cov_type)

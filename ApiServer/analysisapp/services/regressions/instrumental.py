"""
操作変数法 (Instrumental Variables) 分析サービス

linearmodels の IV2SLS による操作変数回帰を提供します。
"""

from typing import Dict, List, Any, Optional
import gc
import pandas as pd
from linearmodels.iv import IV2SLS  # type: ignore

from .base import AbstractRegressionService
from ...utils.validator.common_validators import ValidationError
from ...utils.validator.tables_store_validator import (
    validate_existed_column_name
)
from ..abstract_api import ApiError
from ..django_compat import gettext as _


class IVRegression(AbstractRegressionService):
    """
    操作変数回帰分析クラス

    2段階最小二乗法による操作変数推定を実行します。
    """

    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        instrumental_variables: List[str],
        endogenous_variables: Optional[List[str]] = None,
        **kwargs
    ):
        """
        初期化

        Args:
            table_name: テーブル名
            dependent_variable: 被説明変数の列名
            explanatory_variables: 説明変数の列名リスト（外生変数）
            instrumental_variables: 操作変数の列名リスト
            endogenous_variables: 内生変数の列名リスト
            **kwargs: その他のパラメータ
        """
        super().__init__(
            table_name,
            dependent_variable,
            explanatory_variables,
            **kwargs
        )
        self.instrumental_variables = instrumental_variables
        self.endogenous_variables = endogenous_variables or []
        self.param_names['instrumental_variables'] = 'instrumentalVariables'
        self.param_names['endogenous_variables'] = 'endogenousVariables'

    def _validate_specific(self):
        """
        IV固有のバリデーション
        """
        # 列名リストの取得
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )

        # 操作変数の検証
        if not self.instrumental_variables:
            message = _("At least one instrumental variable is required")
            raise ValidationError(message)

        for iv in self.instrumental_variables:
            validate_existed_column_name(
                iv,
                column_name_list,
                self.param_names['instrumental_variables']
            )

        # 内生変数の検証
        for endog in self.endogenous_variables:
            validate_existed_column_name(
                endog,
                column_name_list,
                self.param_names['endogenous_variables']
            )

        # 操作変数が説明変数や被説明変数と重複していないかチェック
        if self.dependent_variable in self.instrumental_variables:
            raise ValidationError(
                _("Instrumental variables cannot include the "
                  "dependent variable")
            )

        # 識別条件のチェック
        if self.endogenous_variables:
            n_instruments = len(self.instrumental_variables)
            n_endogenous = len(self.endogenous_variables)
            if n_instruments < n_endogenous:
                message = _(
                    "Number of instrumental variables must be greater "
                    "than or equal to number of endogenous variables"
                )
                raise ValidationError(message)

    def fit(self, y_data, x_data, missing: str):
        """
        IVモデルのフィッティング (linearmodels を使用)

        Args:
            y_data: 被説明変数のデータ（使用しない）
            x_data: 説明変数のデータ（使用しない）
            missing: 欠損値の処理方法

        Returns:
            linearmodels の IV2SLS 回帰結果
        """
        # テーブルの取得
        table_info = self.tables_store.get_table(self.table_name)
        df_polars = table_info.table

        # 必要な列を選択
        required_cols = (
            [self.dependent_variable]
            + self.explanatory_variables
            + self.endogenous_variables
            + self.instrumental_variables
        )

        # Pandas DataFrameに変換（PyArrow拡張配列を使用してメモリ効率向上）
        df = df_polars.select(required_cols).to_pandas(
            use_pyarrow_extension_array=True
        )

        # Polars DataFrameを明示的に削除してメモリを解放
        del df_polars
        gc.collect()

        # 欠損値の処理
        if missing == 'drop':
            df = df.dropna()
        elif missing == 'raise':
            if df.isnull().any().any():
                raise ApiError(_("Missing values found in data"))

        if len(df) == 0:
            raise ApiError(_("No valid observations after removing "
                             "missing values"))

        # 被説明変数、外生変数、内生変数、操作変数を設定
        dependent = df[self.dependent_variable]
        exog = df[self.explanatory_variables] if self.explanatory_variables else None
        endog = df[self.endogenous_variables] if self.endogenous_variables else None
        instruments = df[self.instrumental_variables]

        # 標準誤差方法のマッピング
        cov_type_map = {
            'nonrobust': 'unadjusted',
            'hc0': 'robust',
            'hc1': 'robust',
            'hc2': 'robust',
            'hc3': 'robust',
            'hac': 'kernel',
            'clustered': 'clustered'
        }
        cov_type = cov_type_map.get(
            self.standard_error_method, 'unadjusted'
        )

        # IV2SLS モデルの作成とフィット
        model = IV2SLS(dependent, exog, endog, instruments)
        result = model.fit(cov_type=cov_type)

        return result

    def _format_result(self, model_result) -> Dict:
        """
        IV モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: linearmodels の回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary)

        # パラメータの詳細情報
        params_info = []
        all_vars = self.explanatory_variables + self.endogenous_variables
        for i, name in enumerate(all_vars):
            conf_int = model_result.conf_int()
            params_info.append({
                'variable': name,
                'coefficient': float(model_result.params.iloc[i]),
                'standardError': float(model_result.std_errors.iloc[i]),
                'pValue': float(model_result.pvalues.iloc[i]),
                'tValue': float(model_result.tstats.iloc[i]),
                'confidenceIntervalLower': float(conf_int.iloc[i, 0]),
                'confidenceIntervalUpper': float(conf_int.iloc[i, 1])
            })

        # モデル統計情報
        model_stats: Dict[str, Any] = {
            'nObservations': int(model_result.nobs),
            'R2': float(model_result.rsquared)
        }

        # 診断結果 (diagnostics)
        diagnostics: Dict[str, Any] = {}

        # 内生性の検定 (Wu-Hausman test)
        if hasattr(model_result, 'wu_hausman'):
            try:
                wu_test = model_result.wu_hausman()
                diagnostics['wuHausmanTest'] = {
                    'statistic': float(wu_test.stat),
                    'pValue': float(wu_test.pval),
                    'description': 'Test for endogeneity'
                }
            except Exception:
                pass

        # 過剰識別制約の検定 (Sargan/Hansen J test)
        if hasattr(model_result, 'sargan'):
            try:
                sargan = model_result.sargan()
                diagnostics['sarganTest'] = {
                    'statistic': float(sargan.stat),
                    'pValue': float(sargan.pval),
                    'description': 'Test for overidentifying restrictions'
                }
            except Exception:
                pass

        # 弱操作変数の検定 (First-stage F-statistic)
        if hasattr(model_result, 'first_stage'):
            try:
                first_stage = model_result.first_stage
                diagnostics['firstStage'] = {}
                for endog_var in self.endogenous_variables:
                    if endog_var in first_stage.individual:
                        fs_result = first_stage.individual[endog_var]
                        diagnostics['firstStage'][endog_var] = {
                            'fStatistic': float(fs_result.f_stat.stat),
                            'pValue': float(fs_result.f_stat.pval),
                            'description': 'First-stage F-test for weak '
                                          'instruments'
                        }
            except Exception:
                pass

        result = {
            'tableName': self.table_name,
            'dependentVariable': self.dependent_variable,
            'explanatoryVariables': self.explanatory_variables,
            'endogenousVariables': self.endogenous_variables,
            'instrumentalVariables': self.instrumental_variables,
            'regressionResult': summary_text,
            'parameters': params_info,
            'modelStatistics': model_stats,
            'diagnostics': diagnostics
        }

        return result

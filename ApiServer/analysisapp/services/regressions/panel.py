"""
パネルデータ分析サービス

linearmodels を使用した固定効果モデルと変量効果モデルを提供します。
"""

from typing import Dict, List, Any, Optional
import gc
import numpy as np
import polars as pl
import pandas as pd
from linearmodels.panel import PanelOLS, RandomEffects  # type: ignore

from .base import AbstractRegressionService
from ..data.tables_store import TablesStore
from ...utils.validator.common_validators import (
    ValidationError,
    validate_candidates
)
from ...utils.validator.tables_store_validator import (
    validate_existed_column_name
)
from ..abstract_api import ApiError
from ..django_compat import gettext as _


class FixedEffectsRegression(AbstractRegressionService):
    """
    固定効果回帰分析クラス

    linearmodels の PanelOLS を利用した固定効果推定を実行します。
    """

    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        entity_id_column: str,
        time_column: Optional[str] = None,
        standard_error_method: str = 'clustered',
        **kwargs
    ):
        """
        初期化

        Args:
            table_name: テーブル名
            dependent_variable: 被説明変数の列名
            explanatory_variables: 説明変数の列名リスト
            entity_id_column: 個体ID列名
            time_column: 時間列名（オプション）
            standard_error_method: 標準誤差の計算方法
            **kwargs: その他のパラメータ
        """
        super().__init__(
            table_name,
            dependent_variable,
            explanatory_variables,
            standard_error_method=standard_error_method,
            has_const=True,  # PanelOLS は自動的に定数項を処理
            **kwargs
        )
        self.entity_id_column = entity_id_column
        self.time_column = time_column
        self.param_names['entity_id_column'] = 'entityIdColumn'
        self.param_names['time_column'] = 'timeColumn'

        # クラスター標準誤差の場合、groupsが未指定なら entity_id_column を使用
        if (standard_error_method == 'clustered' and
                'groups' not in self.standard_error_params):
            self.standard_error_params['groups'] = entity_id_column

    def _validate_specific(self):
        """
        固定効果モデル固有のバリデーション
        """
        # 列名リストの取得
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )

        # 個体ID列の検証
        validate_existed_column_name(
            self.entity_id_column,
            column_name_list,
            self.param_names['entity_id_column']
        )

        # 個体ID列が説明変数や被説明変数と重複していないかチェック
        if self.entity_id_column == self.dependent_variable:
            raise ValidationError(
                _("Entity ID column cannot be the same as "
                  "dependent variable")
            )
        if self.entity_id_column in self.explanatory_variables:
            raise ValidationError(
                _("Entity ID column cannot be included in "
                  "explanatory variables")
            )

        # 時間列の検証（オプション）
        if self.time_column:
            validate_existed_column_name(
                self.time_column,
                column_name_list,
                self.param_names['time_column']
            )

    def fit(self, y_data, x_data, missing: str):
        """
        固定効果モデルのフィッティング (linearmodels を使用)

        Args:
            y_data: 被説明変数のデータ（使用しない、直接取得）
            x_data: 説明変数のデータ（使用しない、直接取得）
            missing: 欠損値の処理方法

        Returns:
            linearmodels の PanelOLS 回帰結果
        """
        # テーブルの取得
        table_info = self.tables_store.get_table(self.table_name)
        df_polars = table_info.table

        # 必要な列を選択
        required_cols = (
            [self.dependent_variable]
            + self.explanatory_variables
            + [self.entity_id_column]
        )
        if self.time_column:
            required_cols.append(self.time_column)

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

        # MultiIndex の設定
        if self.time_column:
            df = df.set_index([self.entity_id_column, self.time_column])
        else:
            # 時間列がない場合は自動生成
            df['_time'] = df.groupby(self.entity_id_column).cumcount()
            df = df.set_index([self.entity_id_column, '_time'])

        # 被説明変数と説明変数を設定
        y = df[self.dependent_variable]
        X = df[self.explanatory_variables]

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
            self.standard_error_method, 'clustered'
        )

        # PanelOLS モデルの作成とフィット
        model = PanelOLS(y, X, entity_effects=True)
        result = model.fit(cov_type=cov_type)

        return result

    def _format_result(self, model_result) -> Dict:
        """
        固定効果モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: linearmodels の回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary)

        # パラメータの詳細情報
        params_info = []
        for i, name in enumerate(self.explanatory_variables):
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

        # モデル統計情報と診断結果
        model_stats: Dict[str, Any] = {
            'nObservations': int(model_result.nobs),
            'nEntities': int(model_result.entity_info['total']),
            'R2Within': float(model_result.rsquared),
            'R2Between': float(model_result.rsquared_between),
            'R2Overall': float(model_result.rsquared_overall),
            'fValue': float(model_result.f_statistic.stat),
            'fProbability': float(model_result.f_statistic.pval)
        }

        # 診断結果 (diagnostics)
        diagnostics: Dict[str, Any] = {
            'rsquaredWithin': float(model_result.rsquared),
            'rsquaredBetween': float(model_result.rsquared_between),
            'rsquaredOverall': float(model_result.rsquared_overall)
        }

        # 個体効果の有意性検定 (F-test for pooled model)
        if hasattr(model_result, 'f_pooled'):
            diagnostics['fPooled'] = {
                'statistic': float(model_result.f_pooled.stat),
                'pValue': float(model_result.f_pooled.pval),
                'description': 'Test for entity effects'
            }

        result = {
            'tableName': self.table_name,
            'dependentVariable': self.dependent_variable,
            'explanatoryVariables': self.explanatory_variables,
            'entityIdColumn': self.entity_id_column,
            'estimationMethod': 'Fixed Effects (Within)',
            'regressionResult': summary_text,
            'parameters': params_info,
            'modelStatistics': model_stats,
            'diagnostics': diagnostics
        }

        return result


class RandomEffectsRegression(AbstractRegressionService):
    """
    変量効果回帰分析クラス

    linearmodels の RandomEffects モデルを使用します。
    """

    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        entity_id_column: str,
        time_column: Optional[str] = None,
        standard_error_method: str = 'clustered',
        **kwargs
    ):
        """
        初期化

        Args:
            table_name: テーブル名
            dependent_variable: 被説明変数の列名
            explanatory_variables: 説明変数の列名リスト
            entity_id_column: 個体ID列名
            time_column: 時間列名（オプション）
            standard_error_method: 標準誤差の計算方法
            **kwargs: その他のパラメータ
        """
        super().__init__(
            table_name,
            dependent_variable,
            explanatory_variables,
            standard_error_method=standard_error_method,
            has_const=True,
            **kwargs
        )
        self.entity_id_column = entity_id_column
        self.time_column = time_column
        self.param_names['entity_id_column'] = 'entityIdColumn'
        self.param_names['time_column'] = 'timeColumn'

        # クラスター標準誤差の場合、groupsが未指定なら entity_id_column を使用
        if (standard_error_method == 'clustered' and
                'groups' not in self.standard_error_params):
            self.standard_error_params['groups'] = entity_id_column

    def _validate_specific(self):
        """
        変量効果モデル固有のバリデーション
        """
        # 列名リストの取得
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )

        # 個体ID列の検証
        validate_existed_column_name(
            self.entity_id_column,
            column_name_list,
            self.param_names['entity_id_column']
        )

        # 時間列の検証（オプション）
        if self.time_column:
            validate_existed_column_name(
                self.time_column,
                column_name_list,
                self.param_names['time_column']
            )

    def fit(self, y_data, x_data, missing: str):
        """
        変量効果モデルのフィッティング (linearmodels を使用)

        Args:
            y_data: 被説明変数のデータ（使用しない）
            x_data: 説明変数のデータ（使用しない）
            missing: 欠損値の処理方法

        Returns:
            linearmodels の RandomEffects 回帰結果
        """
        # テーブルの取得
        table_info = self.tables_store.get_table(self.table_name)
        df_polars = table_info.table

        # 必要な列を選択
        required_cols = (
            [self.dependent_variable]
            + self.explanatory_variables
            + [self.entity_id_column]
        )
        if self.time_column:
            required_cols.append(self.time_column)

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

        # MultiIndex の設定
        if self.time_column:
            df = df.set_index([self.entity_id_column, self.time_column])
        else:
            df['_time'] = df.groupby(self.entity_id_column).cumcount()
            df = df.set_index([self.entity_id_column, '_time'])

        # 被説明変数と説明変数を設定
        y = df[self.dependent_variable]
        X = df[self.explanatory_variables]

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
            self.standard_error_method, 'clustered'
        )

        # RandomEffects モデルの作成とフィット
        model = RandomEffects(y, X)
        result = model.fit(cov_type=cov_type)

        return result

    def _format_result(self, model_result) -> Dict:
        """
        変量効果モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: linearmodels の回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary)

        # パラメータの詳細情報
        params_info = []
        for i, name in enumerate(self.explanatory_variables):
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

        # モデル統計情報と診断結果
        model_stats: Dict[str, Any] = {
            'nObservations': int(model_result.nobs),
            'R2Within': float(model_result.rsquared),
            'R2Between': float(model_result.rsquared_between),
            'R2Overall': float(model_result.rsquared_overall)
        }

        # 診断結果 (diagnostics)
        diagnostics: Dict[str, Any] = {
            'rsquaredWithin': float(model_result.rsquared),
            'rsquaredBetween': float(model_result.rsquared_between),
            'rsquaredOverall': float(model_result.rsquared_overall)
        }

        # theta (変量効果の重み)
        if hasattr(model_result, 'theta'):
            theta_value = model_result.theta
            # thetaがDataFrameの場合は平均値を取る
            if hasattr(theta_value, 'mean'):
                if hasattr(theta_value, 'values'):
                    # DataFrameまたはSeriesの場合
                    diagnostics['theta'] = float(theta_value.values.mean())
                else:
                    diagnostics['theta'] = float(theta_value.mean())
            else:
                diagnostics['theta'] = float(theta_value)
            diagnostics['thetaDescription'] = (
                'Weight of random effects transformation '
                '(0=pooled, 1=within)'
            )

        result = {
            'tableName': self.table_name,
            'dependentVariable': self.dependent_variable,
            'explanatoryVariables': self.explanatory_variables,
            'entityIdColumn': self.entity_id_column,
            'estimationMethod': 'Random Effects (GLS)',
            'regressionResult': summary_text,
            'parameters': params_info,
            'modelStatistics': model_stats,
            'diagnostics': diagnostics
        }

        return result


def fixed_effects_estimation(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    entity_id_column: str,
    standard_error_method: str = 'normal',
    use_t_distribution: bool = True
) -> Dict:
    """
    固定効果推定を実行する関数（後方互換性のため）

    Args:
        table_name: テーブル名
        dependent_variable: 被説明変数の列名
        explanatory_variables: 説明変数の列名リスト
        entity_id_column: 個体ID列名
        standard_error_method: 標準誤差の計算方法
        use_t_distribution: t分布を使用するかどうか

    Returns:
        固定効果分析結果を含む辞書
    """
    api = FixedEffectsRegression(
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables,
        entity_id_column=entity_id_column,
        standard_error_method=standard_error_method,
        use_t_distribution=use_t_distribution
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result


def variable_effects_estimation(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    entity_id_column: str,
    standard_error_method: str = 'clustered',
    use_t_distribution: bool = True
) -> Dict:
    """
    変量効果推定を実行する関数（後方互換性のため）

    Args:
        table_name: テーブル名
        dependent_variable: 被説明変数の列名
        explanatory_variables: 説明変数の列名リスト
        entity_id_column: 個体ID列名
        standard_error_method: 標準誤差の計算方法
        use_t_distribution: t分布を使用するかどうか

    Returns:
        分析結果を含む辞書
    """
    api = RandomEffectsRegression(
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables,
        entity_id_column=entity_id_column,
        standard_error_method=standard_error_method,
        use_t_distribution=use_t_distribution
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

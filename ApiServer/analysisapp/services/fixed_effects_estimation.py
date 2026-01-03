from typing import Dict, List

import numpy as np
import polars as pl
import statsmodels.api as sm
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import (ValidationError,
                                                     validate_candidates)
from ..utils.validator.statistics_validators import (
    validate_dependent_variable, validate_explanatory_variables)
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name)
from .abstract_api import AbstractApi, ApiError

# 標準誤差計算方法の候補
STANDARD_ERROR_METHODS = ['normal', 'clustered', 'robust', 'hac']


class FixedEffectsEstimation(AbstractApi):
    """
    個体内偏差を利用した固定効果推定を行うためのAPIクラス

    指定されたテーブルの列を使用して固定効果分析を実行します。
    被説明変数（従属変数）1列と説明変数（独立変数）複数列、個体ID列を指定します。
    個体内偏差（個体内の平均からの乖離）を利用した方法で推定を行います。
    """
    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        entity_id_column: str,
        standard_error_method: str = 'normal',
        use_t_distribution: bool = True
    ):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.dependent_variable = dependent_variable
        self.explanatory_variables = explanatory_variables
        self.entity_id_column = entity_id_column
        self.standard_error_method = standard_error_method
        self.use_t_distribution = use_t_distribution
        self.param_names = {
            'table_name': 'tableName',
            'dependent_variable': 'dependentVariable',
            'explanatory_variables': 'explanatoryVariables',
            'entity_id_column': 'entityIdColumn',
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

            # 標準誤差計算方法の検証
            validate_candidates(
                self.standard_error_method,
                self.param_names['standard_error_method'],
                STANDARD_ERROR_METHODS
            )

            return None
        except ValidationError as e:
            return e

    def execute(self) -> Dict:
        try:
            # テーブルの取得
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # データの準備
            all_columns = [self.dependent_variable] \
                + self.explanatory_variables + [self.entity_id_column]

            # 必要な列のみを選択し、欠損値を除去
            working_df = df.select(all_columns).drop_nulls()

            if working_df.height == 0:
                message = _("No valid observations after "
                            "removing missing values")
                raise ApiError(message)

            # 個体IDでグループ化して個体内偏差を計算
            # 各個体の観測数をチェック（固定効果のためには複数の時点が必要）
            entity_counts = working_df.group_by(self.entity_id_column).agg(
                pl.count().alias("n_obs")
            )
            valid_entities = entity_counts.filter(pl.col("n_obs") > 1)

            if valid_entities.height == 0:
                message = _("No entities with multiple observations found. "
                            "Fixed effects requires multiple time periods "
                            "per entity.")
                raise ApiError(message)

            # 有効な個体のみを保持
            valid_entity_ids = valid_entities.select(
                self.entity_id_column).to_series().to_list()
            working_df = working_df.filter(pl.col(
                self.entity_id_column).is_in(valid_entity_ids))

            # 個体内平均を計算
            group_means = working_df.group_by(self.entity_id_column).agg([
                pl.mean(col).alias(f"{col}_mean")
                for col in (
                    [self.dependent_variable] + self.explanatory_variables)
            ])

            # 元のデータと個体内平均をマージ
            working_df = working_df.join(group_means, on=self.entity_id_column)

            # 個体内偏差を計算（within-group demeaning）
            y_demeaned = working_df.select(
                (pl.col(self.dependent_variable) - pl.col(
                    f"{self.dependent_variable}_mean")).alias("y_demeaned")
            ).to_series().to_numpy()

            x_demeaned_list = []
            for var in self.explanatory_variables:
                x_demeaned = working_df.select(
                    (pl.col(var) - pl.col(f"{var}_mean")).alias(
                        f"{var}_demeaned")
                ).to_series().to_numpy()
                x_demeaned_list.append(x_demeaned)

            x_demeaned = np.column_stack(x_demeaned_list)

            # 固定効果回帰の実行（定数項は不要、個体内偏差により除去される）
            model = sm.OLS(y_demeaned, x_demeaned).fit()

            # 標準誤差の調整
            if self.standard_error_method == 'robust':
                model = model.get_robustcov_results(cov_type='HC0')
            elif self.standard_error_method == 'clustered':
                # クラスター標準誤差（個体でクラスター）
                entity_ids = working_df.select(
                    self.entity_id_column).to_series().to_numpy()
                model = model.get_robustcov_results(cov_type='cluster',
                                                    groups=entity_ids)
            elif self.standard_error_method == 'hac':
                # HAC標準誤差（Newey-West）
                model = model.get_robustcov_results(cov_type='HAC', maxlags=1)

            # t統計量またはz統計量の選択
            if self.use_t_distribution:
                p_values = model.pvalues
                t_values = model.tvalues
            else:
                # 正規分布を使用
                from scipy import stats
                t_values = model.params / model.bse
                p_values = 2 * (1 - stats.norm.cdf(np.abs(t_values)))

            # 結果の整理
            summary_text = model.summary().as_text()

            # パラメータの詳細情報
            params_info = []
            for i, name in enumerate(self.explanatory_variables):
                params_info.append({
                    'variable': name,
                    'coefficient': float(model.params[i]),
                    'standardError': float(model.bse[i]),
                    'pValue': float(p_values[i]),
                    'tValue': float(t_values[i])
                })

            # モデル統計情報
            n_entities = len(valid_entity_ids)
            n_obs = int(working_df.height)
            df_resid = n_obs - len(
                self.explanatory_variables) - n_entities + 1  # 固定効果を考慮

            model_stats = {
                'R2': float(model.rsquared),
                'adjustedR2': float(model.rsquared_adj),
                'fValue': float(model.fvalue) if hasattr(
                    model, 'fvalue') else None,
                'fProbability': float(
                    model.f_pvalue) if hasattr(model, 'f_pvalue') else None,
                'nObservations': n_obs,
                'nEntities': n_entities,
                'degreesOfFreedom': df_resid,
                'standardErrorMethod': self.standard_error_method,
                'useTDistribution': self.use_t_distribution
            }

            # 結果を返す
            result = {
                'tableName': self.table_name,
                'dependentVariable': self.dependent_variable,
                'explanatoryVariables': self.explanatory_variables,
                'entityIdColumn': self.entity_id_column,
                'estimationMethod': 'fixed_effects_within_group_demeaning',
                'regressionResult': summary_text,
                'parameters': params_info,
                'modelStatistics': model_stats
            }
            return result

        except ApiError:
            # Re-raise ApiError so it can be handled by the REST layer
            raise
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "fixed effects estimation processing")
            raise ApiError(message) from e


def fixed_effects_estimation(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    entity_id_column: str,
    standard_error_method: str = 'normal',
    use_t_distribution: bool = True
) -> Dict:
    """
    個体内偏差を利用した固定効果推定を実行する関数

    Args:
        table_name: テーブル名
        dependent_variable: 被説明変数の列名
        explanatory_variables: 説明変数の列名リスト
        entity_id_column: 個体ID列名
        standard_error_method: 標準誤差の計算方法
                               ('normal', 'clustered', 'robust', 'hac')
        use_t_distribution: t分布を使用するかどうか

    Returns:
        固定効果分析結果を含む辞書
    """
    api = FixedEffectsEstimation(
        table_name,
        dependent_variable,
        explanatory_variables,
        entity_id_column,
        standard_error_method,
        use_t_distribution
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

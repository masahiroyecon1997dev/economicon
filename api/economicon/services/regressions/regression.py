import gc
from typing import Any, Dict, List, Optional

import numpy as np
import statsmodels.api as sm
from linearmodels.iv import IV2SLS
from linearmodels.panel import PanelOLS, RandomEffects
from py4etrics.tobit import Tobit
from sklearn.linear_model import Lasso, Ridge
from statsmodels.regression.linear_model import RegressionResultsWrapper

from ...i18n.translation import gettext as _
from ..data.analysis_result import AnalysisResult
from ..data.analysis_result_store import AnalysisResultStore
from ...utils.validators.common import ValidationError
from ...utils.validators.statistics import (
    validate_dependent_variable,
    validate_endogenous_variables,
    validate_entity_id_column,
    validate_explanatory_variables,
    validate_instrumental_variables,
    validate_regulalized_hyperparameters,
    validate_standard_error_method,
    validate_time_column,
)
from ...utils.validators.tables_store import (
    validate_existed_table_name,
)
from ..abstract_api import AbstractApi, ApiError
from ..data.tables_store import TablesStore


class Regression(AbstractApi):
    """
    回帰分析を実行するためのAPIクラス

    指定された分析タイプに基づいて、適切な回帰分析を実行します。
    """

    def __init__(
        self,
        type: str,
        method: Optional[str],
        table_name: str,
        name: str,
        description: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        standard_error_method: str,
        standard_error_params: Dict[str, Any],
        hyper_parameters: Dict[str, Any],
        use_t_distribution: bool,
        has_const: bool,
        missing_value_handling: str,
        entity_id_column: str,
        time_column: str,
        instrumental_variables: List[str],
        endogenous_variables: List[str],
        left_censoring_limit: float,
        right_censoring_limit: float,
    ):
        self.tables_store = TablesStore()
        self.table_info = None
        self.type = type
        self.method = method
        self.table_name = table_name
        self.name = name
        self.description = description
        self.dependent_variable = dependent_variable
        self.explanatory_variables = explanatory_variables
        self.standard_error_method = standard_error_method
        self.standard_error_params = standard_error_params
        self.hyper_parameters = hyper_parameters
        self.use_t_distribution = use_t_distribution
        self.has_const = has_const
        self.missing_value_handling = missing_value_handling
        self.entity_id_column = entity_id_column
        self.time_column = time_column
        self.instrumental_variables = instrumental_variables
        self.endogenous_variables = endogenous_variables
        self.left_censoring_limit = left_censoring_limit
        self.right_censoring_limit = right_censoring_limit
        self.param_names = {
            "type": "type",
            "method": "method",
            "table_name": "tableName",
            "name": "name",
            "description": "description",
            "dependent_variable": "dependentVariable",
            "explanatory_variables": "explanatoryVariables",
            "standard_error_method": "standardErrorMethod",
            "standard_error_params": "standardErrorParams",
            "hyper_parameters": "hyperParameters",
            "use_t_distribution": "useTDistribution",
            "has_const": "hasConst",
            "missing_value_handling": "missingValueHandling",
            "entity_id_column": "entityIdColumn",
            "time_column": "timeColumn",
            "instrumental_variables": "instrumentalVariables",
            "endogenous_variables": "endogenousVariables",
            "left_censoring_limit": "leftCensoringLimit",
            "right_censoring_limit": "rightCensoringLimit",
        }

    def validate(self):
        try:
            # テーブル名の検証
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )

            # 列名リストの取得
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )

            # スキーマの取得
            df_schema = self.tables_store.get_column_info_list(self.table_name)

            # 説明変数の検証
            validate_explanatory_variables(
                self.explanatory_variables,
                column_name_list,
                df_schema,
                self.param_names["explanatory_variables"],
            )

            # 被説明変数の検証
            validate_dependent_variable(
                self.dependent_variable,
                column_name_list,
                self.explanatory_variables,
                df_schema,
                self.param_names["dependent_variable"],
            )

            # 標準誤差のパラメータ検証
            validate_standard_error_method(
                self.standard_error_method,
                self.standard_error_params,
                column_name_list,
            )

            # 分析手法ごとの追加検証
            match self.type:
                case "fe" | "re":
                    # 固定効果分析の場合、個体IDと時間列の検証
                    validate_entity_id_column(
                        self.entity_id_column,
                        column_name_list,
                        self.dependent_variable,
                        self.explanatory_variables,
                        self.param_names["entity_id_column"],
                    )
                    validate_time_column(
                        self.time_column,
                        column_name_list,
                        self.dependent_variable,
                        self.explanatory_variables,
                        self.param_names["time_column"],
                    )
                case "iv":
                    # IV分析の場合、操作変数と内生変数の検証
                    validate_instrumental_variables(
                        self.instrumental_variables,
                        column_name_list,
                        self.dependent_variable,
                        self.explanatory_variables,
                        self.param_names["instrumental_variables"],
                    )
                    validate_endogenous_variables(
                        self.endogenous_variables,
                        column_name_list,
                        self.param_names["endogenous_variables"],
                    )
                case "lasso" | "ridge":
                    # ハイパーパラメータの検証
                    validate_regulalized_hyperparameters(
                        self.hyper_parameters,
                        "alpha",
                        self.param_names["hyper_parameters"],
                    )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            # テーブルの取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # データの準備
            y_data = df[self.dependent_variable].to_numpy()
            x_data = df[self.explanatory_variables].to_numpy()
            # 定数項の追加
            if self.has_const:
                x_data = sm.add_constant(x_data)

            # 欠損値の処理を statsmodels の形式に変換
            missing_handling_map = {
                "ignore": "none",
                "remove": "drop",
                "error": "raise",
            }
            missing = missing_handling_map.get(
                self.missing_value_handling, "drop"
            )

            # モデルのフィット
            analysis_result = None
            match self.type:
                case "ols":
                    model_result = self._linear_fit(
                        y_data,
                        x_data,
                        missing,
                    )
                    model_result = self._apply_standard_errors(
                        model_result,
                    )
                    analysis_result = self._format_result(model_result)
                case "logit":
                    model_result = self._logit_fit(
                        y_data,
                        x_data,
                        missing,
                    )
                    model_result = self._apply_standard_errors(
                        model_result,
                    )
                    analysis_result = self._format_result(model_result)
                case "probit":
                    model_result = self._probit_fit(
                        y_data,
                        x_data,
                        missing,
                    )
                    model_result = self._apply_standard_errors(
                        model_result,
                    )
                    analysis_result = self._format_result(model_result)
                case "tobit":
                    model_result = self._tobit_fit(
                        df,
                        missing,
                    )
                    analysis_result = self._tobit_format_result(model_result)
                case "fe":
                    model_result = self._fe_fit(
                        y_data,
                        x_data,
                        missing,
                    )
                    analysis_result = self._fe_format_result(model_result)
                case "re":
                    model_result = self._re_fit(
                        y_data,
                        x_data,
                        missing,
                    )
                    analysis_result = self._re_format_result(model_result)
                case "iv":
                    model_result = self._iv_fit(
                        y_data,
                        x_data,
                        missing,
                    )
                    model_result = self._apply_standard_errors(
                        model_result,
                    )
                    analysis_result = self._iv_format_result(model_result)
                case "feiv":
                    raise NotImplementedError(
                        _("FEIV regression is not yet implemented")
                    )
                case "lasso":
                    model_result = self._lasso_fit(
                        y_data,
                        x_data,
                        missing,
                    )
                    analysis_result = self._format_result(model_result)
                case "ridge":
                    model_result = self._ridge_fit(
                        y_data,
                        x_data,
                        missing,
                    )
                    analysis_result = self._format_result(model_result)
                case _:
                    raise ApiError(
                        _(f"Unsupported regression type: {self.type}")
                    )

            # 分析結果をストアに保存
            analysis_result = AnalysisResult(
                name=self.name or f"{self.type.upper()} Analysis",
                description=self.description,
                table_name=self.table_name,
                regression_output=analysis_result,
            )

            result_store = AnalysisResultStore()
            result_id = result_store.save_result(analysis_result)

            result = {
                "resultId": result_id,
            }
            # IDのみを返却
            return result
        except ApiError as e:
            raise ApiError(str(e))
        except NotImplementedError as e:
            raise NotImplementedError(str(e))
        except Exception as e:
            raise Exception(
                f"Unexpected error: {str(e)}",
            )

    def _linear_fit(
        self,
        y_data,
        x_data,
        missing: str,
    ) -> RegressionResultsWrapper:
        """
        OLSモデルのフィッティング

        Args:
            y_data: 被説明変数のデータ
            x_data: 説明変数のデータ
            missing: 欠損値の処理方法 ('none', 'drop', 'raise')

        Returns:
            statsmodels の OLS 回帰結果
        """
        # OLSモデルの作成とフィット
        model = sm.OLS(y_data, x_data, missing=missing)
        result = model.fit()

        return result

    def _logit_fit(
        self, y_data, x_data, missing: str
    ) -> RegressionResultsWrapper:
        """
        Logitモデルのフィッティング

        Args:
            y_data: 被説明変数のデータ
            x_data: 説明変数のデータ
            missing: 欠損値の処理方法 ('none', 'drop', 'raise')

        Returns:
            statsmodels の Logit 回帰結果
        """
        model = sm.Logit(y_data, x_data, missing=missing)
        result = model.fit()

        return result

    def _probit_fit(
        self, y_data, x_data, missing: str
    ) -> RegressionResultsWrapper:
        """
        Probitモデルのフィッティング

        Args:
            y_data: 被説明変数のデータ
            x_data: 説明変数のデータ
            missing: 欠損値の処理方法 ('none', 'drop', 'raise')

        Returns:
            statsmodels の Probit 回帰結果
        """
        model = sm.Probit(y_data, x_data, missing=missing)
        result = model.fit()

        return result

    def _tobit_fit(self, df_polars, missing: str):
        """
        Tobitモデルのフィッティング (py4etrics を使用)

        Args:
            y_data: 被説明変数のデータ
            x_data: 説明変数のデータ
            missing: 欠損値の処理方法

        Returns:
            py4etrics の Tobit 回帰結果
        """
        # 必要な列を選択
        required_cols = [self.dependent_variable] + self.explanatory_variables

        # Pandas DataFrameに変換
        df = df_polars.select(required_cols).to_pandas()

        # 欠損値の処理
        if missing == "drop":
            df = df.dropna()
        elif missing == "raise":
            if df.isnull().any().any():
                raise ApiError(_("Missing values found in data"))

        if len(df) == 0:
            raise ApiError(
                _("No valid observations after removing missing values")
            )

        # 被説明変数と説明変数を設定
        y = df[self.dependent_variable].values
        X = df[self.explanatory_variables].values

        # 定数項を追加
        if self.has_const:
            X = sm.add_constant(X)

        cens = np.zeros(len(y))
        if self.left_censoring_limit is not None:
            # 実際に打ち切られている行を -1 にする
            cens[y <= self.left_censoring_limit] = -1

        if self.right_censoring_limit is not None:
            # 実際に打ち切られている行を 1 にする
            cens[y >= self.right_censoring_limit] = 1

        # Tobit モデルの作成とフィット
        model = Tobit(
            y,
            X,
            cens=cens,
            left=self.left_censoring_limit,
            right=self.right_censoring_limit,
        )  # type: ignore
        result = model.fit()

        return result

    def _iv_fit(self, y_data, x_data, missing: str):
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
        if missing == "drop":
            df = df.dropna()
        elif missing == "raise":
            if df.isnull().any().any():
                raise ApiError(_("Missing values found in data"))

        if len(df) == 0:
            raise ApiError(
                _("No valid observations after removing missing values")
            )

        # 被説明変数、外生変数、内生変数、操作変数を設定
        dependent = df[self.dependent_variable]
        exog = (
            df[self.explanatory_variables]
            if self.explanatory_variables
            else None
        )
        endog = (
            df[self.endogenous_variables]
            if self.endogenous_variables
            else None
        )
        instruments = df[self.instrumental_variables]

        # 標準誤差方法のマッピング
        cov_type_map = {
            "nonrobust": "unadjusted",
            "hc0": "robust",
            "hc1": "robust",
            "hc2": "robust",
            "hc3": "robust",
            "hac": "kernel",
            "clustered": "clustered",
        }
        cov_type = cov_type_map.get(self.standard_error_method, "unadjusted")

        # IV2SLS モデルの作成とフィット
        model = IV2SLS(dependent, exog, endog, instruments)
        result = model.fit(cov_type=cov_type)

        return result

    def _fe_fit(self, y_data, x_data, missing: str):
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

        # Pandas DataFrameに変換
        # （PyArrow拡張配列を使用してメモリ効率向上）
        df = df_polars.select(required_cols).to_pandas(
            use_pyarrow_extension_array=True
        )

        # Polars DataFrameを明示的に削除してメモリを解放
        del df_polars
        gc.collect()

        # 欠損値の処理
        if missing == "drop":
            df = df.dropna()
        elif missing == "raise":
            if df.isnull().any().any():
                raise ApiError(_("Missing values found in data"))

        if len(df) == 0:
            raise ApiError(
                _("No valid observations after removing missing values")
            )

        # MultiIndex の設定
        if self.time_column:
            df = df.set_index([self.entity_id_column, self.time_column])
        else:
            # 時間列がない場合は自動生成
            df["_time"] = df.groupby(self.entity_id_column).cumcount()
            df = df.set_index([self.entity_id_column, "_time"])

        # 被説明変数と説明変数を設定
        y = df[self.dependent_variable]
        X = df[self.explanatory_variables]

        # 標準誤差方法のマッピング
        cov_type_map = {
            "nonrobust": "unadjusted",
            "hc0": "robust",
            "hc1": "robust",
            "hc2": "robust",
            "hc3": "robust",
            "hac": "kernel",
            "clustered": "clustered",
        }
        cov_type = cov_type_map.get(self.standard_error_method, "clustered")

        # PanelOLS モデルの作成とフィット
        model = PanelOLS(y, X, entity_effects=True)
        result = model.fit(cov_type=cov_type)

        return result

    def _re_fit(self, y_data, x_data, missing: str):
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

        # Pandas DataFrameに変換
        # （PyArrow拡張配列を使用してメモリ効率向上）
        df = df_polars.select(required_cols).to_pandas(
            use_pyarrow_extension_array=True
        )

        # Polars DataFrameを明示的に削除してメモリを解放
        del df_polars
        gc.collect()

        # 欠損値の処理
        if missing == "drop":
            df = df.dropna()
        elif missing == "raise":
            if df.isnull().any().any():
                raise ApiError(_("Missing values found in data"))

        if len(df) == 0:
            raise ApiError(
                _("No valid observations after removing missing values")
            )

        # MultiIndex の設定
        if self.time_column:
            df = df.set_index([self.entity_id_column, self.time_column])
        else:
            df["_time"] = df.groupby(self.entity_id_column).cumcount()
            df = df.set_index([self.entity_id_column, "_time"])

        # 被説明変数と説明変数を設定
        y = df[self.dependent_variable]
        X = df[self.explanatory_variables]

        # 標準誤差方法のマッピング
        cov_type_map = {
            "nonrobust": "unadjusted",
            "hc0": "robust",
            "hc1": "robust",
            "hc2": "robust",
            "hc3": "robust",
            "hac": "kernel",
            "clustered": "clustered",
        }
        cov_type = cov_type_map.get(self.standard_error_method, "clustered")

        # RandomEffects モデルの作成とフィット
        model = RandomEffects(y, X)
        result = model.fit(cov_type=cov_type)

        return result

    def _apply_standard_errors(self, model_result: Any) -> Any:
        """
        標準誤差の計算方法を適用

        Args:
            model_result: 初期の回帰結果

        Returns:
            標準誤差が調整された回帰結果
        """
        if self.standard_error_method == "nonrobust":
            return model_result

        cov_type_map = {
            "hc0": "HC0",
            "hc1": "HC1",
            "hc2": "HC2",
            "hc3": "HC3",
            "hac": "HAC",
            "clustered": "cluster",
        }

        cov_type = cov_type_map.get(self.standard_error_method)
        if not cov_type:
            return model_result

        # HACの場合はmaxlagsを渡す (デフォルトは sqrt(n) に基づく計算)
        if self.standard_error_method == "hac":
            maxlags = self.standard_error_params.get("maxlags")
            if maxlags is None:
                # maxlagsが未指定の場合、デフォルト値を計算
                import numpy as np

                table_info = self.tables_store.get_table(self.table_name)
                n = len(table_info.table)
                maxlags = int(np.floor(4 * (n / 100) ** (2 / 9)))
            return model_result.get_robustcov_results(
                cov_type=cov_type, maxlags=maxlags
            )

        # クラスタリングの場合は groups を渡す
        if self.standard_error_method == "clustered":
            groups_col = self.standard_error_params.get("groups")
            if groups_col:
                table_info = self.tables_store.get_table(self.table_name)
                df = table_info.table
                groups = df[groups_col].to_numpy()
                return model_result.get_robustcov_results(
                    cov_type=cov_type, groups=groups
                )

        return model_result.get_robustcov_results(cov_type=cov_type)

    def _lasso_fit(
        self, y_data, x_data, missing: str
    ) -> RegressionResultsWrapper:
        """
        Lassoモデルのフィッティング

        Args:
            y_data: 被説明変数のデータ
            x_data: 説明変数のデータ（定数項が含まれる可能性あり）
            missing: 欠損値の処理方法

        Returns:
            statsmodels 互換の回帰結果
        """
        alpha = self.hyper_parameters.get("alpha", 1.0)

        # x_dataに定数項が含まれている場合は除去
        # （scikit-learnはfit_interceptで定数項を扱うため）
        x_data_sklearn = x_data
        if self.has_const:
            # 最初の列が定数項かチェック（全て1の列）
            if x_data.shape[1] > 0 and np.allclose(x_data[:, 0], 1.0):
                x_data_sklearn = x_data[:, 1:]  # 定数項を除去

        # scikit-learn の Lasso を使用
        lasso = Lasso(alpha=alpha, fit_intercept=self.has_const)
        lasso.fit(x_data_sklearn, y_data)

        # statsmodels 形式で再構築（統計量を取得するため）
        # Lassoの予測値を使ってOLSで統計量を計算
        model = sm.OLS(y_data, x_data, missing=missing)
        result = model.fit()

        # Lasso の係数で上書き
        if self.has_const:
            result._results.params = np.hstack(
                ([lasso.intercept_], lasso.coef_)  # type: ignore
            )
        else:
            result._results.params = lasso.coef_

        return result

    def _ridge_fit(
        self, y_data, x_data, missing: str
    ) -> RegressionResultsWrapper:
        """
        Ridgeモデルのフィッティング

        Args:
            y_data: 被説明変数のデータ
            x_data: 説明変数のデータ（定数項が含まれる可能性あり）
            missing: 欠損値の処理方法

        Returns:
            statsmodels 互換の回帰結果
        """
        alpha = self.hyper_parameters.get("alpha", 1.0)

        # x_dataに定数項が含まれている場合は除去
        # （scikit-learnはfit_interceptで定数項を扱うため）
        x_data_sklearn = x_data
        if self.has_const:
            # 最初の列が定数項かチェック（全て1の列）
            if x_data.shape[1] > 0 and np.allclose(x_data[:, 0], 1.0):
                x_data_sklearn = x_data[:, 1:]  # 定数項を除去

        # scikit-learn の Ridge を使用
        ridge = Ridge(alpha=alpha, fit_intercept=self.has_const)
        ridge.fit(x_data_sklearn, y_data)

        # statsmodels 形式で再構築（統計量を取得するため）
        # Ridgeの予測値を使ってOLSで統計量を計算
        model = sm.OLS(y_data, x_data, missing=missing)
        result = model.fit()

        # Ridge の係数で上書き
        if self.has_const:
            result._results.params = np.hstack(
                ([ridge.intercept_], ridge.coef_)  # type: ignore
            )
        else:
            result._results.params = ridge.coef_

        return result

    def _format_result(self, model_result: Any) -> Dict:
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
            ["const"] if self.has_const else []
        ) + self.explanatory_variables
        params_info = []

        for i, name in enumerate(param_names):
            param_dict = {
                "variable": name,
                "coefficient": float(model_result.params[i]),
                "standardError": float(model_result.bse[i]),
                "pValue": float(model_result.pvalues[i]),
            }

            # t値またはz値
            if hasattr(model_result, "tvalues"):
                param_dict["tValue"] = float(model_result.tvalues[i])

            # 信頼区間
            if hasattr(model_result, "conf_int"):
                conf_int = model_result.conf_int()
                param_dict["confidenceIntervalLower"] = float(conf_int[i, 0])
                param_dict["confidenceIntervalUpper"] = float(conf_int[i, 1])

            params_info.append(param_dict)

        # モデル統計情報
        model_stats: Dict[str, Any] = {"nObservations": int(model_result.nobs)}

        # 線形モデルの統計量
        if hasattr(model_result, "rsquared"):
            model_stats["R2"] = float(model_result.rsquared)
        if hasattr(model_result, "rsquared_adj"):
            model_stats["adjustedR2"] = float(model_result.rsquared_adj)
        if hasattr(model_result, "fvalue"):
            model_stats["fValue"] = float(model_result.fvalue)
        if hasattr(model_result, "f_pvalue"):
            model_stats["fProbability"] = float(model_result.f_pvalue)

        # 共通の統計量
        if hasattr(model_result, "aic"):
            model_stats["AIC"] = float(model_result.aic)
        if hasattr(model_result, "bic"):
            model_stats["BIC"] = float(model_result.bic)
        if hasattr(model_result, "llf"):
            model_stats["logLikelihood"] = float(model_result.llf)

        # 離散選択モデルの統計量
        if hasattr(model_result, "prsquared"):
            model_stats["pseudoRSquared"] = float(model_result.prsquared)

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
        }

        return result

    def _tobit_format_result(self, model_result) -> Dict:
        """
        Tobit モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: py4etrics の Tobit 回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary())

        # パラメータの詳細情報
        param_names = (
            ["const"] if self.has_const else []
        ) + self.explanatory_variables
        params_info = []

        for i, name in enumerate(param_names):
            params_info.append(
                {
                    "variable": name,
                    "coefficient": float(model_result.params[i]),
                    "standardError": float(model_result.bse[i]),
                    "pValue": float(model_result.pvalues[i]),
                    "tValue": float(model_result.tvalues[i]),
                }
            )

        # モデル統計情報
        model_stats: Dict[str, Any] = {
            "nObservations": int(model_result.nobs),
            "logLikelihood": float(model_result.llf),
        }

        # AIC, BIC があれば追加
        if hasattr(model_result, "aic"):
            model_stats["AIC"] = float(model_result.aic)
        if hasattr(model_result, "bic"):
            model_stats["BIC"] = float(model_result.bic)

        # 診断結果 (diagnostics)
        diagnostics: Dict[str, Any] = {
            "censoringLimits": {
                "left": self.left_censoring_limit,
                "right": self.right_censoring_limit,
            }
        }

        # sigma (誤差項の標準偏差)
        if hasattr(model_result, "scale"):
            diagnostics["sigma"] = float(model_result.scale)
            diagnostics["sigmaDescription"] = (
                "Standard error of the error term"
            )

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
            "diagnostics": diagnostics,
        }

        return result

    def _iv_format_result(self, model_result) -> Dict:
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
            params_info.append(
                {
                    "variable": name,
                    "coefficient": float(model_result.params.iloc[i]),
                    "standardError": float(model_result.std_errors.iloc[i]),
                    "pValue": float(model_result.pvalues.iloc[i]),
                    "tValue": float(model_result.tstats.iloc[i]),
                    "confidenceIntervalLower": float(conf_int.iloc[i, 0]),
                    "confidenceIntervalUpper": float(conf_int.iloc[i, 1]),
                }
            )

        # モデル統計情報
        model_stats: Dict[str, Any] = {
            "nObservations": int(model_result.nobs),
            "R2": float(model_result.rsquared),
        }

        # 診断結果 (diagnostics)
        diagnostics: Dict[str, Any] = {}

        # 内生性の検定 (Wu-Hausman test)
        if hasattr(model_result, "wu_hausman"):
            try:
                wu_test = model_result.wu_hausman()
                diagnostics["wuHausmanTest"] = {
                    "statistic": float(wu_test.stat),
                    "pValue": float(wu_test.pval),
                    "description": "Test for endogeneity",
                }
            except Exception:
                pass

        # 過剰識別制約の検定 (Sargan/Hansen J test)
        if hasattr(model_result, "sargan"):
            try:
                sargan = model_result.sargan()
                diagnostics["sarganTest"] = {
                    "statistic": float(sargan.stat),
                    "pValue": float(sargan.pval),
                    "description": "Test for overidentifying restrictions",
                }
            except Exception:
                pass

        # 弱操作変数の検定 (First-stage F-statistic)
        if hasattr(model_result, "first_stage"):
            try:
                first_stage = model_result.first_stage
                diagnostics["firstStage"] = {}
                for endog_var in self.endogenous_variables:
                    if endog_var in first_stage.individual:
                        fs_result = first_stage.individual[endog_var]
                        diagnostics["firstStage"][endog_var] = {
                            "fStatistic": float(fs_result.f_stat.stat),
                            "pValue": float(fs_result.f_stat.pval),
                            "description": "First-stage F-test for weak instruments",
                        }
            except Exception:
                pass

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "endogenousVariables": self.endogenous_variables,
            "instrumentalVariables": self.instrumental_variables,
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
            "diagnostics": diagnostics,
        }

        return result

    def _fe_format_result(self, model_result) -> Dict:
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
            params_info.append(
                {
                    "variable": name,
                    "coefficient": float(model_result.params.iloc[i]),
                    "standardError": float(model_result.std_errors.iloc[i]),
                    "pValue": float(model_result.pvalues.iloc[i]),
                    "tValue": float(model_result.tstats.iloc[i]),
                    "confidenceIntervalLower": float(conf_int.iloc[i, 0]),
                    "confidenceIntervalUpper": float(conf_int.iloc[i, 1]),
                }
            )

        # モデル統計情報と診断結果
        model_stats: Dict[str, Any] = {
            "nObservations": int(model_result.nobs),
            "nEntities": int(model_result.entity_info["total"]),
            "R2Within": float(model_result.rsquared),
            "R2Between": float(model_result.rsquared_between),
            "R2Overall": float(model_result.rsquared_overall),
            "fValue": float(model_result.f_statistic.stat),
            "fProbability": float(model_result.f_statistic.pval),
        }

        # 診断結果 (diagnostics)
        diagnostics: Dict[str, Any] = {
            "rsquaredWithin": float(model_result.rsquared),
            "rsquaredBetween": float(model_result.rsquared_between),
            "rsquaredOverall": float(model_result.rsquared_overall),
        }

        # 個体効果の有意性検定 (F-test for pooled model)
        if hasattr(model_result, "f_pooled"):
            diagnostics["fPooled"] = {
                "statistic": float(model_result.f_pooled.stat),
                "pValue": float(model_result.f_pooled.pval),
                "description": "Test for entity effects",
            }

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "entityIdColumn": self.entity_id_column,
            "estimationMethod": "Fixed Effects (Within)",
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
            "diagnostics": diagnostics,
        }

        return result

    def _re_format_result(self, model_result) -> Dict:
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
            params_info.append(
                {
                    "variable": name,
                    "coefficient": float(model_result.params.iloc[i]),
                    "standardError": float(model_result.std_errors.iloc[i]),
                    "pValue": float(model_result.pvalues.iloc[i]),
                    "tValue": float(model_result.tstats.iloc[i]),
                    "confidenceIntervalLower": float(conf_int.iloc[i, 0]),
                    "confidenceIntervalUpper": float(conf_int.iloc[i, 1]),
                }
            )

        # モデル統計情報と診断結果
        model_stats: Dict[str, Any] = {
            "nObservations": int(model_result.nobs),
            "R2Within": float(model_result.rsquared),
            "R2Between": float(model_result.rsquared_between),
            "R2Overall": float(model_result.rsquared_overall),
        }

        # 診断結果 (diagnostics)
        diagnostics: Dict[str, Any] = {
            "rsquaredWithin": float(model_result.rsquared),
            "rsquaredBetween": float(model_result.rsquared_between),
            "rsquaredOverall": float(model_result.rsquared_overall),
        }

        # theta (変量効果の重み)
        if hasattr(model_result, "theta"):
            theta_value = model_result.theta
            # thetaがDataFrameの場合は平均値を取る
            if hasattr(theta_value, "mean"):
                if hasattr(theta_value, "values"):
                    # DataFrameまたはSeriesの場合
                    diagnostics["theta"] = float(theta_value.values.mean())
                else:
                    diagnostics["theta"] = float(theta_value.mean())
            else:
                diagnostics["theta"] = float(theta_value)
            diagnostics["thetaDescription"] = (
                "Weight of random effects transformation (0=pooled, 1=within)"
            )

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "entityIdColumn": self.entity_id_column,
            "estimationMethod": "Random Effects (GLS)",
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
            "diagnostics": diagnostics,
        }

        return result

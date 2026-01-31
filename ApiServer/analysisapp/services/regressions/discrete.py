"""
離散選択モデル分析サービス

Logit, Probit, Tobit モデルによる離散選択分析を提供します。
"""

from typing import Any, Dict, List, Optional

import statsmodels.api as sm
from py4etrics.tobit import Tobit
from statsmodels.regression.linear_model import RegressionResultsWrapper

from ...i18n.translation import gettext as _
from ..abstract_api import ApiError
from .base import AbstractRegressionService

# Check if py4etrics is available
try:
    from py4etrics.tobit import Tobit  # noqa: F811

    PY4ETRICS_AVAILABLE = True
except ImportError:
    PY4ETRICS_AVAILABLE = False


class LogitRegression(AbstractRegressionService):
    """
    ロジット回帰分析クラス

    ロジスティック回帰による二値選択モデルを実行します。
    """

    def _validate_specific(self):
        """
        Logit固有のバリデーション

        現時点では追加の検証は不要です。
        """
        pass

    def fit(self, y_data, x_data, missing: str) -> RegressionResultsWrapper:
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

        # 標準誤差の調整を適用
        result = self._apply_standard_errors(result)

        return result


class ProbitRegression(AbstractRegressionService):
    """
    プロビット回帰分析クラス

    プロビット回帰による二値選択モデルを実行します。
    """

    def _validate_specific(self):
        """
        Probit固有のバリデーション

        現時点では追加の検証は不要です。
        """
        pass

    def fit(self, y_data, x_data, missing: str) -> RegressionResultsWrapper:
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

        # 標準誤差の調整を適用
        result = self._apply_standard_errors(result)

        return result


class TobitRegression(AbstractRegressionService):
    """
    トービット回帰分析クラス

    打ち切りデータを扱うトービットモデルを実行します。
    """

    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        left_censoring_limit: Optional[float] = 0.0,
        right_censoring_limit: Optional[float] = None,
        **kwargs,
    ):
        """
        初期化

        Args:
            table_name: テーブル名
            dependent_variable: 被説明変数の列名
            explanatory_variables: 説明変数の列名リスト
            left_censoring_limit: 左側打ち切り値（デフォルトは0.0）
            right_censoring_limit: 右側打ち切り値
            **kwargs: その他のパラメータ
        """
        super().__init__(
            table_name, dependent_variable, explanatory_variables, **kwargs
        )
        self.left_censoring_limit = left_censoring_limit
        self.right_censoring_limit = right_censoring_limit
        self.param_names.update(
            {
                "left_censoring_limit": "leftCensoringLimit",
                "right_censoring_limit": "rightCensoringLimit",
            }
        )

    def _validate_specific(self):
        """
        Tobit固有のバリデーション
        """
        if not PY4ETRICS_AVAILABLE:
            raise ValueError(
                _(
                    "py4etrics library is required for Tobit regression. "
                    "Please install it with: uv add py4etrics"
                )
            )

    def fit(self, y_data, x_data, missing: str):
        """
        Tobitモデルのフィッティング (py4etrics を使用)

        Args:
            y_data: 被説明変数のデータ
            x_data: 説明変数のデータ
            missing: 欠損値の処理方法

        Returns:
            py4etrics の Tobit 回帰結果
        """
        # テーブルの取得
        table_info = self.tables_store.get_table(self.table_name)
        df_polars = table_info.table

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
            raise ApiError(_("No valid observations after removing missing values"))

        # 被説明変数と説明変数を設定
        y = df[self.dependent_variable].values
        X = df[self.explanatory_variables].values

        # 定数項を追加
        if self.has_const:
            X = sm.add_constant(X)

        # 打ち切り設定
        cens = (self.left_censoring_limit, self.right_censoring_limit)

        # Tobit モデルの作成とフィット
        model = Tobit(y, X, cens=cens)  # type: ignore
        result = model.fit()

        return result  # type: ignore

    def _format_result(self, model_result) -> Dict:
        """
        Tobit モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: py4etrics の Tobit 回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary())

        # パラメータの詳細情報
        param_names = (["const"] if self.has_const else []) + self.explanatory_variables
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
            diagnostics["sigmaDescription"] = "Standard error of the error term"

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


def logistic_regression(
    table_name: str, dependent_variable: str, explanatory_variables: List[str], **kwargs
) -> Dict:
    """
    ロジスティック回帰分析を実行する関数（後方互換性のため）

    Args:
        table_name: テーブル名
        dependent_variable: 被説明変数の列名
        explanatory_variables: 説明変数の列名リスト
        **kwargs: 追加のパラメータ

    Returns:
        分析結果を含む辞書
    """
    api = LogitRegression(
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables,
        **kwargs,
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result


def probit_regression(
    table_name: str, dependent_variable: str, explanatory_variables: List[str], **kwargs
) -> Dict:
    """
    プロビット回帰分析を実行する関数（後方互換性のため）

    Args:
        table_name: テーブル名
        dependent_variable: 被説明変数の列名
        explanatory_variables: 説明変数の列名リスト
        **kwargs: 追加のパラメータ

    Returns:
        分析結果を含む辞書
    """
    api = ProbitRegression(
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables,
        **kwargs,
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
    return result

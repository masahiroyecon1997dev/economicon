"""
正則化回帰分析サービス

Lasso (L1正則化) と Ridge (L2正則化) 回帰を提供します。
"""

from typing import Dict, List, Any, Optional
import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import Lasso, Ridge  # type: ignore
from statsmodels.regression.linear_model import RegressionResultsWrapper

from .base import AbstractRegressionService
from ...utils.validator.common_validators import ValidationError
from ..abstract_api import ApiError
from ..django_compat import gettext as _


class LassoRegression(AbstractRegressionService):
    """
    Lasso回帰分析クラス

    L1正則化による変数選択を行う回帰分析を実行します。
    """

    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        hyper_parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初期化

        Args:
            table_name: テーブル名
            dependent_variable: 被説明変数の列名
            explanatory_variables: 説明変数の列名リスト
            hyper_parameters: ハイパーパラメータ (alpha等)
            **kwargs: その他のパラメータ
        """
        super().__init__(
            table_name,
            dependent_variable,
            explanatory_variables,
            **kwargs
        )
        self.hyper_parameters = hyper_parameters or {}
        self.param_names['hyper_parameters'] = 'hyperParameters'

    def _validate_specific(self):
        """
        Lasso固有のバリデーション
        """
        # alpha パラメータの検証
        if 'alpha' not in self.hyper_parameters:
            message = _(
                "hyperParameters に alpha (正則化パラメータ) が必要です"
            )
            raise ValidationError(message)

        alpha = self.hyper_parameters.get('alpha')
        if not isinstance(alpha, (int, float)) or alpha < 0:
            message = _("alpha must be a numeric value greater than or "
                        "equal to 0")
            raise ValidationError(message)

    def fit(
        self,
        y_data,
        x_data,
        missing: str
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
        alpha = self.hyper_parameters.get('alpha', 1.0)

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


class RidgeRegression(AbstractRegressionService):
    """
    Ridge回帰分析クラス

    L2正則化による回帰分析を実行します。
    """

    def __init__(
        self,
        table_name: str,
        dependent_variable: str,
        explanatory_variables: List[str],
        hyper_parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初期化

        Args:
            table_name: テーブル名
            dependent_variable: 被説明変数の列名
            explanatory_variables: 説明変数の列名リスト
            hyper_parameters: ハイパーパラメータ (alpha等)
            **kwargs: その他のパラメータ
        """
        super().__init__(
            table_name,
            dependent_variable,
            explanatory_variables,
            **kwargs
        )
        self.hyper_parameters = hyper_parameters or {}
        self.param_names['hyper_parameters'] = 'hyperParameters'

    def _validate_specific(self):
        """
        Ridge固有のバリデーション
        """
        # alpha パラメータの検証
        if 'alpha' not in self.hyper_parameters:
            message = _(
                "hyperParameters requires 'alpha' "
                "(regularization parameter)"
            )
            raise ValidationError(message)

        alpha = self.hyper_parameters.get('alpha')
        if not isinstance(alpha, (int, float)) or alpha < 0:
            message = _("alpha must be a numeric value greater than or "
                        "equal to 0")
            raise ValidationError(message)

    def fit(
        self,
        y_data,
        x_data,
        missing: str
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
        alpha = self.hyper_parameters.get('alpha', 1.0)

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

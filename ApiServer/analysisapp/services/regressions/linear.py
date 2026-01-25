"""
線形回帰分析サービス

OLS (Ordinary Least Squares) による線形回帰分析を提供します。
"""

from typing import Dict, List, Any, Optional
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper

from .base import AbstractRegressionService
from ..django_compat import gettext as _


class OLSRegression(AbstractRegressionService):
    """
    OLS線形回帰分析クラス

    最小二乗法による線形回帰分析を実行します。
    """

    def _validate_specific(self):
        """
        OLS固有のバリデーション

        現時点では追加の検証は不要です。
        """
        pass

    def fit(
        self,
        y_data,
        x_data,
        missing: str
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

        # 標準誤差の調整を適用
        result = self._apply_standard_errors(result)

        return result


def linear_regression(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: List[str],
    **kwargs
) -> Dict:
    """
    線形回帰分析を実行する関数（後方互換性のため）

    Args:
        table_name: テーブル名
        dependent_variable: 被説明変数の列名
        explanatory_variables: 説明変数の列名リスト
        **kwargs: 追加のパラメータ

    Returns:
        分析結果を含む辞書
    """
    api = OLSRegression(
        table_name=table_name,
        dependent_variable=dependent_variable,
        explanatory_variables=explanatory_variables,
        **kwargs
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

"""
標準誤差の計算と適用

回帰分析の標準誤差計算方法を適用する関数を提供します。
"""

from typing import Any

from .common import STATSMODELS_COV_TYPE_MAP


def apply_standard_errors(
    model_result: Any,
    standard_error_method: str,
    standard_error_params: dict,
) -> Any:
    """
    標準誤差の計算方法を適用

    Args:
        model_result: 初期の回帰結果
        standard_error_method: 標準誤差の計算方法
        standard_error_params: 標準誤差のパラメータ

    Returns:
        標準誤差が調整された回帰結果
    """
    # nonrobustの場合は何も調整せずそのまま返す
    if standard_error_method == "nonrobust":
        return model_result

    cov_type = STATSMODELS_COV_TYPE_MAP.get(standard_error_method)
    # Noneまたは存在しない場合は調整なし
    if not cov_type:
        return model_result

    # HACの場合はmaxlagsを渡す (デフォルトは sqrt(n) に基づく計算)
    if standard_error_method == "hac":
        maxlags = standard_error_params.get("maxlags")
        if maxlags is None:
            import numpy as np

            n = model_result.nobs
            maxlags = int(np.floor(4 * (n / 100) ** (2 / 9)))
        return model_result.get_robustcov_results(
            cov_type=cov_type, maxlags=maxlags
        )

    # クラスタリングの場合は groups を渡す
    if standard_error_method == "clustered":
        groups = standard_error_params.get("groups")
        if groups is None:
            return model_result
        return model_result.get_robustcov_results(cov_type=cov_type, groups=groups)

    return model_result.get_robustcov_results(cov_type=cov_type)

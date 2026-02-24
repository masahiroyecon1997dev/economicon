"""
標準誤差の計算と適用

回帰分析の標準誤差計算方法を適用する関数を提供します。
"""

from typing import Any

from economicon.models import (
    ClusteredStandardError,
    HacStandardError,
    RobustStandardError,
    StandardErrorSettings,
)


def apply_standard_errors(
    model_result: Any, standard_error_settings: StandardErrorSettings
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
    match standard_error_settings:
        case RobustStandardError():
            model_result = model_result.get_robustcov_results(
                cov_type=standard_error_settings.hc_type
            )

        case ClusteredStandardError():
            model_result = model_result.get_robustcov_results(
                cov_type=standard_error_settings.method,
                groups=standard_error_settings.groups,
                use_correction=standard_error_settings.use_correction,
            )
        case HacStandardError():
            maxlags = standard_error_settings.maxlags
            model_result = model_result.get_robustcov_results(
                cov_type=standard_error_settings.method,
                maxlags=maxlags,
                use_correction=standard_error_settings.use_correction,
            )
    return model_result

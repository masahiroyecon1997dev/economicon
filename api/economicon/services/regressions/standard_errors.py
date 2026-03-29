"""
標準誤差の計算と適用

回帰分析の標準誤差計算方法を適用する関数を提供します。
"""

from typing import Any

import numpy as np

from economicon.schemas import (
    ClusteredStandardError,
    HacStandardError,
    RobustStandardError,
    StandardErrorSettings,
)


def get_discrete_fit_kwargs(
    standard_error_settings: StandardErrorSettings,
    groups_arrays: dict[str, np.ndarray] | None = None,
) -> dict:
    """Logit/Probit の DiscreteResults.fit() に渡す
    cov_type と cov_kwds を構築する。

    OLS には使用しない。OLS は fit() 後に get_robustcov_results() を呼ぶ
    apply_standard_errors() を使うこと。

    Args:
        standard_error_settings: 標準誤差の設定
        groups_arrays: ClusteredStandardError 用の欠損値除去済み配列辞書。
            build_groups_arrays() の戻り値をそのまま渡すこと。

    Returns:
        ``model.fit(**kwargs)`` に展開できる辞書。
        キーは ``cov_type`` と ``cov_kwds``。
    """
    match standard_error_settings:
        case RobustStandardError():
            return {
                "cov_type": standard_error_settings.hc_type,
                "cov_kwds": {},
            }
        case ClusteredStandardError():
            cols = standard_error_settings.groups
            if groups_arrays is not None:
                resolved: np.ndarray = (
                    groups_arrays[cols[0]]
                    if len(cols) == 1
                    else np.column_stack([groups_arrays[c] for c in cols])
                )
            else:
                resolved = np.asarray(cols)  # type: ignore[arg-type]
            return {
                "cov_type": standard_error_settings.method,
                "cov_kwds": {
                    "groups": resolved,
                    "use_correction": standard_error_settings.use_correction,
                },
            }
        case HacStandardError():
            return {
                "cov_type": standard_error_settings.method,
                "cov_kwds": {
                    "maxlags": standard_error_settings.maxlags,
                    "use_correction": standard_error_settings.use_correction,
                },
            }
        case _:
            return {"cov_type": "nonrobust", "cov_kwds": {}}


def apply_standard_errors(
    model_result: Any,
    standard_error_settings: StandardErrorSettings,
    groups_arrays: dict[str, np.ndarray] | None = None,
) -> Any:
    """
    OLS 結果に標準誤差の計算方法を適用する。

    Logit/Probit (DiscreteResults) には使用しない。
    DiscreteResults は get_discrete_fit_kwargs() で
    フィット時に SE を指定すること。

    Args:
        model_result: 初期の回帰結果 (RegressionResultsWrapper)
        standard_error_settings: 標準誤差の設定
        groups_arrays: クラスター標準誤差用の実データ配列辞書。
            {``列名``: numpy 配列} の形式。欠損値除去後の行数と一致すること。
            None の場合は settings.groups (列名文字列) をそのまま渡す。

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
            cols = standard_error_settings.groups
            if groups_arrays is not None:
                # 列名を欠損値除去済みの numpy 配列に解決する
                if len(cols) == 1:
                    resolved: np.ndarray = groups_arrays[cols[0]]
                else:
                    resolved = np.column_stack(
                        [groups_arrays[c] for c in cols]
                    )
            else:
                # フォールバック: 列名文字列をそのまま渡す（旧振る舞い）
                resolved = np.asarray(cols)  # type: ignore[arg-type]
            model_result = model_result.get_robustcov_results(
                cov_type=standard_error_settings.method,
                groups=resolved,
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

"""
RDD 推定ヘルパー関数

- rdrobust 呼び出し・結果抽出
- rddensity (McCrary) 密度検定
- Polars によるビンデータ生成
- 核重み付き局所多項式フィット評価
- プラシーボテスト
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.utils import ProcessingError
from economicon.utils.column_names import generate_unique_column_name

# ---------------------------------------------------------------------------
# rdrobust 共通パラメータ集約クラス
# ---------------------------------------------------------------------------


@dataclass
class RDDRunConfig:
    """
    rdrobust 呼び出しに共通するパラメータ群。

    run_placebo_tests など引数が多い関数の引数数削減に使用する。
    """

    cutoff: float
    kernel: str
    bw_select: str
    h: float | None
    p: int
    vce: str
    level: int


# ---------------------------------------------------------------------------
# カーネル重み計算
# ---------------------------------------------------------------------------


def _kernel_weights(
    x: np.ndarray,
    cutoff: float,
    bandwidth: float,
    kernel: str,
) -> np.ndarray:
    """
    カーネル重みを計算する。

    Eco-Note: rdrobust と同一のカーネル関数を使用することで、
    poly_fit_data の曲線が rdrobust 推定値と整合する。
    u = (x - c) / h として |u| <= 1 の範囲のみ非ゼロ重みを持つ。

    Parameters
    ----------
    x : np.ndarray
        実行変数の値
    cutoff : float
        カットオフ値
    bandwidth : float
        バンド幅 h
    kernel : str
        カーネル種別 ('triangular' / 'epanechnikov' / 'uniform')

    Returns
    -------
    np.ndarray
        各観測のカーネル重み（非負）
    """
    u = (x - cutoff) / bandwidth
    mask = np.abs(u) <= 1.0
    if kernel == "triangular":
        w = np.where(mask, 1.0 - np.abs(u), 0.0)
    elif kernel == "epanechnikov":
        # Eco-Note: エパネチニコフカーネルは MSE 最適カーネルだが、
        # 三角カーネルが RDD の標準的選択。
        w = np.where(mask, 0.75 * (1.0 - u**2), 0.0)
    else:  # uniform
        w = np.where(mask, 1.0, 0.0)
    return w


# ---------------------------------------------------------------------------
# 局所多項式フィット
# ---------------------------------------------------------------------------


def _fit_local_poly(
    x: np.ndarray,
    y: np.ndarray,
    cutoff: float,
    bandwidth: float,
    p: int,
    kernel: str,
    side: str,
) -> np.ndarray | None:
    """
    カーネル加重局所多項式 WLS を実行してフィット係数を返す。

    Eco-Note: rdrobust の内部推定式と同一の局所多項式 WLS。
      fitted(x) = β₀ + β₁(x-c) + β₂(x-c)² + ... + βₚ(x-c)ᵖ
    β₀ がカットオフ限界値（= RDD 推定値の構成要素）。

    Parameters
    ----------
    x : np.ndarray
        実行変数
    y : np.ndarray
        結果変数
    cutoff : float
        カットオフ値
    bandwidth : float
        バンド幅 h
    p : int
        多項式次数
    kernel : str
        カーネル種別
    side : str
        'left' または 'right'

    Returns
    -------
    np.ndarray | None
        多項式係数 [β₀, β₁, ..., βₚ]。
        推定不能（サンプル不足・特異行列）の場合 None。
    """
    if side == "left":
        mask = (x < cutoff) & (x >= cutoff - bandwidth)
    else:
        mask = (x >= cutoff) & (x <= cutoff + bandwidth)

    x_side = x[mask]
    y_side = y[mask]

    if len(x_side) < p + 2:  # noqa: PLR2004
        return None

    xc = x_side - cutoff
    # デザイン行列: [1, (x-c), (x-c)^2, ..., (x-c)^p]
    x_mat = np.column_stack([xc**j for j in range(p + 1)])
    w = _kernel_weights(x_side, cutoff, bandwidth, kernel)

    if w.sum() == 0:
        return None

    # WLS: (X'WX)^{-1} X'Wy
    w_sqrt = np.sqrt(w)
    xw = x_mat * w_sqrt[:, np.newaxis]
    yw = y_side * w_sqrt
    try:
        beta, _, _, _ = np.linalg.lstsq(xw, yw, rcond=None)
    except np.linalg.LinAlgError:
        return None

    return beta


def compute_poly_fit_data(
    y: np.ndarray,
    x: np.ndarray,
    cutoff: float,
    bw_left: float,
    bw_right: float,
    p: int,
    kernel: str,
    n_points: int = 100,
) -> dict[str, Any]:
    """
    カットオフ左右それぞれで局所多項式フィット曲線を計算する。

    Parameters
    ----------
    y : np.ndarray
        結果変数
    x : np.ndarray
        実行変数
    cutoff : float
        カットオフ値
    bw_left : float
        左側メインバンド幅
    bw_right : float
        右側メインバンド幅
    p : int
        多項式次数
    kernel : str
        カーネル種別
    n_points : int
        各サイドのグリッド点数

    Returns
    -------
    dict
        {"left": {"x": [...], "y": [...]}, "right": {"x": [...], "y": [...]}}
    """

    def _make_side(side: str, bandwidth: float) -> dict[str, list[float]]:
        beta = _fit_local_poly(x, y, cutoff, bandwidth, p, kernel, side)
        if side == "left":
            grid = np.linspace(cutoff - bandwidth, cutoff, n_points)
        else:
            grid = np.linspace(cutoff, cutoff + bandwidth, n_points)

        if beta is None:
            return {"x": [], "y": []}

        xc = grid - cutoff
        x_grid_mat = np.column_stack([xc**j for j in range(p + 1)])
        y_fit = x_grid_mat @ beta
        return {
            "x": grid.tolist(),
            "y": y_fit.tolist(),
        }

    return {
        "left": _make_side("left", bw_left),
        "right": _make_side("right", bw_right),
    }


# ---------------------------------------------------------------------------
# ビンデータ生成
# ---------------------------------------------------------------------------


def compute_bins_data(
    df_pl: pl.DataFrame,
    outcome_var: str,
    running_var: str,
    cutoff: float,
    n_bins: int,
) -> list[dict[str, float]]:
    """
    実行変数を等幅ビンに分割し、各ビンの x 平均値と y 平均値を返す。

    カットオフを境に左右独立にビン化することで境界の不連続が
    散布図で視覚的に確認できる。

    Parameters
    ----------
    df_pl : pl.DataFrame
        分析対象データフレーム
    outcome_var : str
        結果変数列名
    running_var : str
        実行変数列名
    cutoff : float
        カットオフ値
    n_bins : int
        左右合計ビン数

    Returns
    -------
    list[dict]
        [{"x": float, "y": float}, ...] (x 昇順)
    """
    n_left_bins = n_bins // 2
    n_right_bins = n_bins - n_left_bins
    bins: list[dict[str, float]] = []
    bin_col = generate_unique_column_name(
        "__rdd_internal_bin_index__",
        {running_var, outcome_var},
    )

    for side_filter, n_side in [
        (pl.col(running_var) < cutoff, n_left_bins),
        (pl.col(running_var) >= cutoff, n_right_bins),
    ]:
        side_df = df_pl.filter(side_filter).select([running_var, outcome_var])
        if side_df.is_empty():
            continue

        x_min = float(side_df[running_var].min())  # type: ignore[arg-type]
        x_max = float(side_df[running_var].max())  # type: ignore[arg-type]
        if x_min == x_max:
            bins.append({"x": x_min, "y": float(side_df[outcome_var].mean())})  # type: ignore[arg-type]
            continue

        bin_width = (x_max - x_min) / n_side
        agg = (
            side_df.with_columns(
                (
                    ((pl.col(running_var) - x_min) / bin_width)
                    .floor()
                    .clip(upper_bound=n_side - 1)
                    .cast(pl.Int32)
                ).alias(bin_col)
            )
            .group_by(bin_col)
            .agg(
                [
                    pl.col(running_var).mean().alias("x"),
                    pl.col(outcome_var).mean().alias("y"),
                ]
            )
            .sort("x")
        )
        for row in agg.iter_rows(named=True):
            bins.append({"x": float(row["x"]), "y": float(row["y"])})

    bins.sort(key=lambda d: d["x"])
    return bins


# ---------------------------------------------------------------------------
# rdrobust 実行
# ---------------------------------------------------------------------------


def run_rdrobust(
    y: np.ndarray,
    x: np.ndarray,
    *,
    cutoff: float,
    kernel: str,
    bw_select: str,
    h: float | None,
    p: int,
    vce: str,
    level: int,
) -> Any:
    """
    rdrobust を実行して結果オブジェクトを返す。

    Eco-Note: rdrobust は conventional / bias-corrected / robust の
    3 種類の推定値を返す。bias-corrected 推定値は局所 p+1 次多項式で
    バイアス項を推定し、conventional 推定値から引いたもの。
    信頼区間は robust CI（bias-corrected 点推定 + robust SE）を推奨。

    Parameters
    ----------
    level : int
        信頼区間水準 (0-100)。rdrobust に直接渡す。

    Raises
    ------
    ProcessingError
        推定失敗（サンプル不足・特異行列等）の場合
    """
    try:
        from rdrobust import rdrobust as _rdrobust  # noqa: PLC0415

        kwargs: dict[str, Any] = {
            "c": cutoff,
            "kernel": kernel,
            "bwselect": bw_select,
            "p": p,
            "vce": vce,
            "level": level,
            "all": True,
        }
        if h is not None:
            kwargs["h"] = h

        return _rdrobust(y=y, x=x, **kwargs)
    except ProcessingError:
        raise
    except Exception as exc:
        raise ProcessingError(
            error_code=ErrorCode.RDD_PROCESS_ERROR,
            message=_("RDD estimation failed: {}").format(str(exc)),
            detail=str(exc),
        ) from exc


def extract_rdrobust_results(result: Any) -> dict[str, Any]:
    """
    rdrobust 結果オブジェクトから推定統計値を抽出する。

    rdrobust Python の result オブジェクトは numpy 配列または
    pandas DataFrame の属性を持つ。防御的に np.asarray() で変換する。

    Eco-Note:
        coef[0] = conventional（局所 p 次多項式の係数）
        coef[1] = bias-corrected（p+1 次バイアス項を補正）
        coef[2] = robust（= bias-corrected 点推定値）
        se[2]   = robust SE
        t[2]    = robust z 統計量（bias-corrected / robust SE）
        pv[2]   = robust p 値（Calonico et al. 2014 推奨）
        ci[0, :] = conventional CI
        ci[2, :] = robust CI（bias-corrected 点推定 + robust SE）
        rho     = h / b（バンド幅比率）
    """
    coef = np.asarray(result.coef).flatten()
    se = np.asarray(result.se).flatten()
    z_stat = np.asarray(result.t).flatten()
    pv = np.asarray(result.pv).flatten()
    ci = np.asarray(result.ci)  # shape (3, 2)
    bws = np.asarray(result.bws)  # shape (2, 2)

    # conventional
    conv_coef = float(coef[0])
    conv_se = float(se[0])
    conv_z = float(z_stat[0])
    conv_pv = float(pv[0])
    conv_ci_lower = float(ci[0, 0])
    conv_ci_upper = float(ci[0, 1])

    # bias-corrected 点推定値（coef[1] または coef[2]）
    bc_coef = float(coef[1]) if len(coef) > 1 else conv_coef

    # Eco-Note: robust z 統計量・p 値は行インデックス 2。
    # Calonico et al. (2014) が推奨する推論は
    # bias-corrected 点推定 + robust SE に基づく。
    # 行インデックス 2 が存在しない場合は 1 → 0 の順にフォールバック。
    if len(z_stat) >= 3:  # noqa: PLR2004
        bc_z = float(z_stat[2])
        bc_pv = float(pv[2])
    elif len(z_stat) >= 2:  # noqa: PLR2004
        bc_z = float(z_stat[1])
        bc_pv = float(pv[1])
    else:
        bc_z = float("nan")
        bc_pv = float("nan")

    # robust CI（行インデックス 2）または bias-corrected CI（行インデックス 1）
    if ci.shape[0] >= 3:  # noqa: PLR2004
        bc_ci_lower = float(ci[2, 0])
        bc_ci_upper = float(ci[2, 1])
    elif ci.shape[0] >= 2:  # noqa: PLR2004
        bc_ci_lower = float(ci[1, 0])
        bc_ci_upper = float(ci[1, 1])
    else:
        bc_ci_lower = float("nan")
        bc_ci_upper = float("nan")

    # バンド幅: bws[0] = h (main), bws[1] = b (bias)
    h_left = float(bws[0, 0])
    h_right = float(bws[0, 1])
    b_left = float(bws[1, 0])
    b_right = float(bws[1, 1])

    # Eco-Note: rho = h / b。rdrobust が結果に rho 属性を持つ場合は優先使用。
    rho_val: float
    if hasattr(result, "rho") and result.rho is not None:
        rho_arr = np.asarray(result.rho).flatten()
        rho_val = float(rho_arr[0])
    else:
        rho_val = h_left / b_left if b_left != 0 else float("nan")

    # サンプル数: N_h = バンド幅内有効サンプル数
    n_left, n_right, n_total = _extract_sample_sizes(result)

    return {
        "conv_coef": conv_coef,
        "conv_se": conv_se,
        "conv_z": conv_z,
        "conv_pv": conv_pv,
        "conv_ci_lower": conv_ci_lower,
        "conv_ci_upper": conv_ci_upper,
        "bc_coef": bc_coef,
        "bc_z": bc_z,
        "bc_pv": bc_pv,
        "bc_ci_lower": bc_ci_lower,
        "bc_ci_upper": bc_ci_upper,
        "rho": rho_val,
        "h_left": h_left,
        "h_right": h_right,
        "b_left": b_left,
        "b_right": b_right,
        "n_left": n_left,
        "n_right": n_right,
        "n_total": n_total,
    }


def _extract_sample_sizes(result: Any) -> tuple[int, int, int]:
    """
    rdrobust 結果から有効サンプル数と全サンプル数を抽出する。

    rdrobust Python の属性名は版によって異なる可能性があるため
    複数の候補属性を試みる。
    """
    # 全サンプル数
    n_total = 0
    if hasattr(result, "N"):
        n_arr = np.asarray(result.N).flatten()
        if len(n_arr) >= 2:  # noqa: PLR2004
            n_total = int(n_arr[0]) + int(n_arr[1])
        elif len(n_arr) == 1:
            n_total = int(n_arr[0])

    # バンド幅内有効サンプル数
    n_left, n_right = 0, 0
    for attr in ("N_h", "Nh", "N_eff"):
        if hasattr(result, attr):
            nh_arr = np.asarray(getattr(result, attr)).flatten()
            if len(nh_arr) >= 2:  # noqa: PLR2004
                n_left = int(nh_arr[0])
                n_right = int(nh_arr[1])
                break

    # N_h が取れなかった場合は全サンプル数の半分を代入（フォールバック）
    if n_left == 0 and n_right == 0 and hasattr(result, "N"):
        n_arr = np.asarray(result.N).flatten()
        if len(n_arr) >= 2:  # noqa: PLR2004
            n_left = int(n_arr[0])
            n_right = int(n_arr[1])

    return n_left, n_right, n_total


# ---------------------------------------------------------------------------
# McCrary 密度検定 (rddensity)
# ---------------------------------------------------------------------------


def run_density_test(
    x: np.ndarray,
    cutoff: float,
) -> dict[str, Any] | None:
    """
    rddensity による McCrary 密度検定を実行する。

    帰無仮説 H0: カットオフにおいて実行変数の密度は連続（操作なし）。
    p 値が小さい（例: < 0.05）場合はサンプル操作の可能性を示す。

    Parameters
    ----------
    x : np.ndarray
        実行変数
    cutoff : float
        カットオフ値

    Returns
    -------
    dict | None
        {"test_statistic": float, "p_value": float, "description": str}
        rddensity が利用不可の場合は None。
    """
    try:
        from rddensity import rddensity  # noqa: PLC0415

        rd = rddensity(X=x, c=cutoff)  # type: ignore[arg-type]
        test = rd.test

        # test は dict または DataFrame または SimpleNamespace の可能性
        if isinstance(test, dict):
            t_stat = float(
                test.get("t_jk", test.get("statistic", float("nan")))
            )
            p_val = float(test.get("p_jk", test.get("p_value", float("nan"))))
        elif hasattr(test, "t_jk"):
            t_stat = float(test.t_jk)
            p_val = float(test.p_jk)
        else:
            # pandas DataFrame 形式 (index = 行名, 列 = 統計量)
            test_arr = np.asarray(test).flatten()
            t_stat = float(test_arr[0]) if len(test_arr) > 0 else float("nan")
            p_val = float(test_arr[1]) if len(test_arr) > 1 else float("nan")

        if p_val > 0.05:  # noqa: PLR2004
            desc = (
                "Non-significant p-value supports no manipulation "
                "at the cutoff (RDD validity supported)."
            )
        else:
            desc = (
                "Significant p-value may indicate manipulation "
                "at the cutoff (RDD validity in question)."
            )

        return {
            "test_statistic": t_stat,
            "p_value": p_val,
            "description": desc,
        }
    except ImportError:
        return None
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# プラシーボ検定
# ---------------------------------------------------------------------------


def _default_placebo_cutoffs(
    x: np.ndarray,
    cutoff: float,
) -> list[float]:
    """
    プラシーボ境界値のデフォルトを自動生成する。

    実行変数の総範囲の ±5% をカットオフから左右に置く。
    これにより処置・対照それぞれの内側で偽境界を検定できる。

    Eco-Note: プラシーボカットオフは処置割り当て範囲内（left: x < cutoff,
    right: x >= cutoff）に置くことで、local 推定の安定性を確認する。
    """
    x_min = float(x.min())
    x_max = float(x.max())
    span = x_max - x_min
    if span == 0:
        return []
    offset = span * 0.05
    left_placebo = cutoff - offset
    right_placebo = cutoff + offset
    result = []
    if left_placebo > x_min:
        result.append(left_placebo)
    if right_placebo < x_max:
        result.append(right_placebo)
    return result


def run_placebo_tests(
    y: np.ndarray,
    x: np.ndarray,
    *,
    config: RDDRunConfig,
    placebo_cutoffs: list[float] | None,
) -> list[dict[str, Any]]:
    """
    指定された偽境界値でRDD推定を実行しプラシーボ検定を行う。

    プラシーボ境界で有意な推定値が得られた場合、それは偶然の
    不連続または交絡要因の存在を示唆する。
    本来の RDD 推定値が有意かつプラシーボが非有意であることが
    識別戦略の妥当性を支持する。

    Parameters
    ----------
    config : RDDRunConfig
        rdrobust 共通パラメータ。
    placebo_cutoffs : list[float] | None
        None の場合は _default_placebo_cutoffs() で自動生成する。

    Returns
    -------
    list[dict]
        プラシーボ検定結果のリスト。失敗した境界値はスキップする。
    """
    if placebo_cutoffs is None:
        placebo_cutoffs = _default_placebo_cutoffs(x, config.cutoff)

    results: list[dict[str, Any]] = []
    for pc in placebo_cutoffs:
        try:
            from rdrobust import rdrobust as _rdrobust  # noqa: PLC0415

            kwargs: dict[str, Any] = {
                "c": pc,
                "kernel": config.kernel,
                "bwselect": config.bw_select,
                "p": config.p,
                "vce": config.vce,
                "level": config.level,
                "all": False,
            }
            if config.h is not None:
                kwargs["h"] = config.h

            pr = _rdrobust(y=y, x=x, **kwargs)
            pr_coef = np.asarray(pr.coef).flatten()
            pr_se = np.asarray(pr.se).flatten()
            pr_pv = np.asarray(pr.pv).flatten()
            pr_ci = np.asarray(pr.ci)

            pv = float(pr_pv[0])
            results.append(
                {
                    "cutoff": pc,
                    "coef": float(pr_coef[0]),
                    "std_err": float(pr_se[0]),
                    "p_value": pv,
                    "ci_lower": float(pr_ci[0, 0]),
                    "ci_upper": float(pr_ci[0, 1]),
                    "is_significant": pv < 0.05,  # noqa: PLR2004
                }
            )
        except Exception:  # noqa: BLE001
            # 境界値付近でサンプルが不足している場合はスキップ
            continue

    return results

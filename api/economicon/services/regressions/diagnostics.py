"""
回帰診断列の抽出ユーティリティ

推定済みモデルオブジェクト（statsmodels / linearmodels / sklearn）から
予測値・残差などの診断値を Polars DataFrame として返す純粋関数群。
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

import numpy as np
import polars as pl
from scipy.stats import norm as scipy_norm

if TYPE_CHECKING:
    from economicon.services.regressions.fitters import RegularizedResult

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 診断値抽出オプション
# ---------------------------------------------------------------------------


@dataclass
class DiagnosticExtractOptions:
    """extract_from_* 関数に共通する診断値抽出オプション。"""

    dep_var: str
    existing_cols: list[str] = field(default_factory=list)
    target: Literal["fitted", "residual", "both"] = "both"
    standardized: bool = False
    include_interval: bool = False


@dataclass
class TobitExtractConfig:
    """Tobit モデル固有の診断値抽出パラメータ。"""

    row_indices: np.ndarray | None = None
    fitted_type: Literal["latent", "observable"] = "latent"
    left_censoring_limit: float | None = None
    right_censoring_limit: float | None = None


@dataclass
class PanelExtractConfig:
    """パネルモデル固有の診断値抽出パラメータ。"""

    entity_id_column: str
    time_column: str
    fe_type: Literal["total", "within"] = "total"


# ---------------------------------------------------------------------------
# 列名ユーティリティ
# ---------------------------------------------------------------------------


def resolve_column_name(existing_cols: list[str], base: str) -> str:
    """
    列名の衝突を解決し、安全な列名を返す。

    既存の列名リストに ``base`` が含まれない場合はそのまま返す。
    含まれる場合は ``{base}_0``, ``{base}_1``, ... と順番にチェックし、
    最初に空きのある名前を返す。

    Args:
        existing_cols: 現在テーブルに存在する列名のリスト
        base: 衝突チェックの起点となる列名

    Returns:
        衝突しない（または最初に見つかった空きの）列名

    Examples:
        >>> resolve_column_name(["wage", "wage_fitted"], "wage_fitted")
        'wage_fitted_0'
        >>> resolve_column_name(["wage"], "wage_fitted")
        'wage_fitted'
    """
    if base not in existing_cols:
        return base
    i = 0
    while True:
        candidate = f"{base}_{i}"
        if candidate not in existing_cols:
            return candidate
        i += 1


def _build_col_names(
    options: DiagnosticExtractOptions,
    supports_interval: bool = False,
    supports_standardized: bool = False,
) -> dict[str, str]:
    """
    必要な列名をまとめて解決して辞書で返す。

    返り値のキーは内部キー（"fitted", "resid" 等）、
    値は実際にテーブルに追加する列名。

    Args:
        options: 共通の診断値抽出オプション
        supports_interval: モデルが信頼区間をサポートするか
        supports_standardized: モデルが標準化残差をサポートするか

    Returns:
        内部キー → 解決済み列名 の辞書
    """
    resolved: dict[str, str] = {}
    # 作業用に「決定済み列名を追加した仮リスト」を用意し、
    # 同一バッチ内での衝突も回避する。
    working_cols = list(options.existing_cols)

    def _add(key: str, base: str) -> None:
        name = resolve_column_name(working_cols, base)
        resolved[key] = name
        working_cols.append(name)

    if options.target in ("fitted", "both"):
        _add("fitted", f"{options.dep_var}_fitted")
        if options.include_interval and supports_interval:
            _add("fitted_lower_95", f"{options.dep_var}_fitted_lower_95")
            _add("fitted_upper_95", f"{options.dep_var}_fitted_upper_95")

    if options.target in ("residual", "both"):
        _add("resid", f"{options.dep_var}_resid")
        if options.standardized and supports_standardized:
            _add("resid_std", f"{options.dep_var}_resid_std")

    return resolved


def _extract_statsmodels_ci(
    model: object,
    col_map: dict[str, str],
    n: int,
) -> dict[str, pl.Series]:
    """statsmodels 予測値 95% CI を抽出して Series 辞書で返す。

    Warning#6: statsmodels バージョンにより
    ``summary_frame()`` のキー名が異なるため動的に判定する。
    信頼区間の取得に失敗した場合は None 列を返す。
    """
    data: dict[str, pl.Series] = {}
    try:
        sf = model.get_prediction().summary_frame(  # type: ignore[union-attr]
            alpha=0.05
        )
        lower_key = (
            "mean_ci_lower" if "mean_ci_lower" in sf.columns else "ci_lower"
        )
        upper_key = (
            "mean_ci_upper" if "mean_ci_upper" in sf.columns else "ci_upper"
        )
        if "fitted_lower_95" in col_map:
            data[col_map["fitted_lower_95"]] = pl.Series(
                col_map["fitted_lower_95"],
                sf[lower_key].to_numpy(),
                dtype=pl.Float64,
            )
        if "fitted_upper_95" in col_map:
            data[col_map["fitted_upper_95"]] = pl.Series(
                col_map["fitted_upper_95"],
                sf[upper_key].to_numpy(),
                dtype=pl.Float64,
            )
    except Exception:
        # 信頼区間が取得できない場合（Logit/Probit 等）は None 列
        if "fitted_lower_95" in col_map:
            data[col_map["fitted_lower_95"]] = pl.Series(
                col_map["fitted_lower_95"],
                [None] * n,
                dtype=pl.Float64,
            )
        if "fitted_upper_95" in col_map:
            data[col_map["fitted_upper_95"]] = pl.Series(
                col_map["fitted_upper_95"],
                [None] * n,
                dtype=pl.Float64,
            )
    return data


def _extract_statsmodels_resid(
    model: object,
    col_map: dict[str, str],
    n: int,
    residual_type: Literal["raw", "deviance"],
) -> dict[str, pl.Series]:
    """statsmodels 残差を抽出して Series 辞書で返す。

    Eco-Note A: ``residual_type="deviance"`` の場合、
    Logit/Probit の deviance 残差（``model.resid_dev``）を使用する。
    ``resid_dev`` を持たないモデル（OLS 等）は raw にフォールバック。
    """
    data: dict[str, pl.Series] = {}
    if "resid" in col_map:
        use_deviance = residual_type == "deviance" and hasattr(
            model, "resid_dev"
        )
        if use_deviance:
            try:
                resid = np.asarray(
                    model.resid_dev,  # type: ignore[union-attr]
                    dtype=np.float64,
                )
            except Exception:
                resid = np.asarray(
                    model.resid,  # type: ignore[union-attr]
                    dtype=np.float64,
                )
        elif hasattr(model, "resid"):
            resid = np.asarray(
                model.resid,  # type: ignore[union-attr]
                dtype=np.float64,
            )
        else:
            # Logit/Probit は .resid を持たず .resid_response (y - p̂) を使う
            resid = np.asarray(
                model.resid_response,  # type: ignore[union-attr]
                dtype=np.float64,
            )
        data[col_map["resid"]] = pl.Series(
            col_map["resid"], resid, dtype=pl.Float64
        )
    if "resid_std" in col_map:
        try:
            resid_std = np.asarray(
                model.get_influence().resid_studentized_internal,  # type: ignore[union-attr]
                dtype=np.float64,
            )
            data[col_map["resid_std"]] = pl.Series(
                col_map["resid_std"], resid_std, dtype=pl.Float64
            )
        except Exception:
            data[col_map["resid_std"]] = pl.Series(
                col_map["resid_std"], [None] * n, dtype=pl.Float64
            )
    return data


# ---------------------------------------------------------------------------
# statsmodels（OLS / Logit / Probit）
# ---------------------------------------------------------------------------


def _get_statsmodels_row_indices(model: object) -> np.ndarray:
    """
    statsmodels の結果オブジェクトから元テーブルの行番号（0-based）を復元する。

    statsmodels 0.14+ では、numpy 配列を入力とした場合、
    ``fittedvalues`` は pandas Series ではなく numpy.ndarray を返す。
    そのため、行番号の取得方法をオブジェクトの型に応じて切り替える。

    - **pandas Series の場合**: ``.index.to_numpy()`` で元の行番号を取得
    - **numpy.ndarray の場合**: ``model.data.missing_row_idx`` を使用して
      欠損行を除いた元テーブルの行番号を再構築する

    Args:
        model: statsmodels の fit 済み結果オブジェクト

    Returns:
        元テーブルにおける推定使用行の 0-based 整数インデックス配列
    """
    fittedvalues = model.fittedvalues  # type: ignore[union-attr]

    if hasattr(fittedvalues, "index"):
        # pandas Series: index が元テーブルの行番号そのもの
        return fittedvalues.index.to_numpy().astype(np.int64)

    # numpy.ndarray: missing_row_idx から欠損行を除き再構築
    data_obj = getattr(getattr(model, "model", model), "data", None)  # type: ignore[union-attr]
    missing_list: list[int] = getattr(data_obj, "missing_row_idx", None) or []

    n_fitted = len(fittedvalues)
    n_original = n_fitted + len(missing_list)
    missing_set = set(missing_list)
    return np.array(
        [i for i in range(n_original) if i not in missing_set],
        dtype=np.int64,
    )


def extract_from_statsmodels(
    model: object,
    options: DiagnosticExtractOptions,
    residual_type: Literal["raw", "deviance"] = "raw",
) -> tuple[pl.DataFrame, list[str]]:
    """
    statsmodels の回帰結果から診断値を抽出する。

    Parameters
    ----------
    model:
        ``statsmodels`` の ``RegressionResultsWrapper``
        （または互換の fitted result オブジェクト）。
    options:
        共通の診断値抽出オプション。
    residual_type:
        残差種別。``"deviance"`` の場合は Logit/Probit deviance 残差を使用。

    Returns
    -------
    tuple[pl.DataFrame, list[str]]
        - DataFrame: ``__row_idx__`` 列（欠損除去後の行番号）と
          解決済み列名を持つ Polars DataFrame。
        - list[str]: 実際に追加される列名のリスト（追加順）。

    Notes
    -----
    ``fittedvalues.index`` は statsmodels が欠損除去後に振り直した
    整数インデックス（0-based）なので、そのまま ``__row_idx__`` として
    元テーブルとの ``left_join`` キーに使用できる。
    """
    col_map = _build_col_names(
        options,
        supports_interval=True,
        supports_standardized=True,
    )

    index = _get_statsmodels_row_indices(model)
    n = len(index)
    data: dict[str, pl.Series] = {
        "__row_idx__": pl.Series("__row_idx__", index, dtype=pl.Int64)
    }

    if "fitted" in col_map:
        fitted = np.asarray(
            model.fittedvalues,  # type: ignore[union-attr]
            dtype=np.float64,
        )
        data[col_map["fitted"]] = pl.Series(
            col_map["fitted"], fitted, dtype=pl.Float64
        )

    if "fitted_lower_95" in col_map or "fitted_upper_95" in col_map:
        data.update(_extract_statsmodels_ci(model, col_map, n))

    data.update(_extract_statsmodels_resid(model, col_map, n, residual_type))

    df = pl.DataFrame(data)
    added_cols = list(col_map.values())
    return df, added_cols


# ---------------------------------------------------------------------------
# Tobit（py4etrics）
# ---------------------------------------------------------------------------


def extract_from_tobit(
    model: object,
    options: DiagnosticExtractOptions,
    tobit_config: TobitExtractConfig | None = None,
) -> tuple[pl.DataFrame, list[str]]:
    """
    py4etrics の Tobit 回帰結果から診断値を抽出する。

    Parameters
    ----------
    model:
        ``py4etrics.Tobit`` の fitted result オブジェクト。
    options:
        共通の診断値抽出オプション。
    tobit_config:
        Tobit 固有パラメータ（row_indices / fitted_type / 打ち切り値）。
        ``None`` の場合はデフォルト値（latent / 打ち切りなし）を使用。

    Returns
    -------
    tuple[pl.DataFrame, list[str]]
        - DataFrame: ``__row_idx__`` と解決済み列名を持つ Polars DataFrame。
        - list[str]: 追加された列名のリスト。

    Notes
    -----
    Eco-Note B: Tobit の予測値には 2 種類ある:

    **latent** (デフォルト):
        潜在変数の線形インデックス x'β̂。

    **observable** (左側打ち切り L のみ, z = (x'β̂ - L)/σ̂):
        E[y|x] = L·Φ(-z) + x'β̂·Φ(z) + σ̂·φ(z)

    **observable** (右側打ち切り U のみ, z = (U - x'β̂)/σ̂):
        E[y|x] = x'β̂·Φ(z) - σ̂·φ(z) + U·(1-Φ(z))

    両側打ち切りの場合は latent にフォールバックする。
    """
    cfg = tobit_config or TobitExtractConfig()
    # Tobit は standardized / include_interval 未サポート
    _opts = DiagnosticExtractOptions(
        dep_var=options.dep_var,
        existing_cols=options.existing_cols,
        target=options.target,
    )
    col_map = _build_col_names(_opts)

    # py4etrics Tobit: .fittedvalues は潜在変数の
    # 線形インデックス x'β を numpy.ndarray で返す
    # .predict() は NotImplementedError を投げるため使用しない
    latent_arr = np.asarray(
        model.fittedvalues,  # type: ignore[union-attr]
        dtype=np.float64,
    )
    n = len(latent_arr)

    # Eco-Note B: observable モードで打ち切りを考慮した E[y|x] を計算
    # - 片側打ち切りのみ対応（両側は latent にフォールバック）
    if cfg.fitted_type == "observable":
        left_lim = cfg.left_censoring_limit
        right_lim = cfg.right_censoring_limit
        sigma = float(  # type: ignore[union-attr]
            getattr(model, "scale", None) or 1.0
        )
        if left_lim is not None and right_lim is None:
            # 左側打ち切りのみ: E[y|x] = L·Φ(-z) + x'β·Φ(z) + σ·φ(z)
            z = (latent_arr - left_lim) / sigma
            fitted_arr = (
                left_lim * scipy_norm.cdf(-z)
                + latent_arr * scipy_norm.cdf(z)
                + sigma * scipy_norm.pdf(z)
            )
        elif right_lim is not None and left_lim is None:
            # 右側打ち切りのみ: E[y|x] = x'β·Φ(z) - σ·φ(z) + U·(1-Φ(z))
            z = (right_lim - latent_arr) / sigma
            fitted_arr = (
                latent_arr * scipy_norm.cdf(z)
                - sigma * scipy_norm.pdf(z)
                + right_lim * scipy_norm.cdf(-z)
            )
        else:
            # 両側または情報なし: latent にフォールバック
            _logger.warning(
                "Tobit observable fitted values not supported for "
                "double-sided censoring; falling back to latent values."
            )
            fitted_arr = latent_arr
    else:
        fitted_arr = latent_arr

    # Critical#3: row_indices が提供された場合は
    # 元テーブルの欠損除去後の行 ID を使用する。
    # pandas.dropna() が元の整数インデックスを保持するため、
    # np.arange(n) で代替すると行ズレが発生する。
    if cfg.row_indices is not None:
        index = cfg.row_indices.astype(np.int64)
    else:
        index = np.arange(n, dtype=np.int64)

    data: dict[str, pl.Series] = {
        "__row_idx__": pl.Series("__row_idx__", index, dtype=pl.Int64)
    }

    if "fitted" in col_map:
        data[col_map["fitted"]] = pl.Series(
            col_map["fitted"], fitted_arr, dtype=pl.Float64
        )

    if "resid" in col_map:
        # .resid = endog - fittedvalues (latent ベース)
        resid_raw = np.asarray(model.resid, dtype=np.float64)  # type: ignore[union-attr]
        if cfg.fitted_type == "observable" and fitted_arr is not latent_arr:
            # observable の場合は視測値 - E[y|x] で残差を再計算
            # endog は model.model.endog または求まる場合は raw 残差を利用
            endog = np.asarray(
                getattr(getattr(model, "model", model), "endog", None)  # type: ignore[union-attr]
                or model.resid + latent_arr,  # type: ignore[union-attr]
                dtype=np.float64,
            )
            resid = endog - fitted_arr
        else:
            resid = resid_raw
        data[col_map["resid"]] = pl.Series(
            col_map["resid"], resid, dtype=pl.Float64
        )

    df = pl.DataFrame(data)
    added_cols = list(col_map.values())
    return df, added_cols


# ---------------------------------------------------------------------------
# linearmodels パネルデータ（FE / RE）
# ---------------------------------------------------------------------------


def extract_from_linearmodels_panel(
    model: object,
    options: DiagnosticExtractOptions,
    panel_config: PanelExtractConfig,
) -> tuple[pl.DataFrame, list[str]]:
    """
    linearmodels のパネル回帰結果から診断値を抽出する。

    Parameters
    ----------
    model:
        ``linearmodels.panel.PanelEffectsResults``
        または ``RandomEffectsResults``。
    options:
        共通の診断値抽出オプション。
    panel_config:
        パネルモデル固有パラメータ
        （entity_id_column / time_column / fe_type）。

    Returns
    -------
    tuple[pl.DataFrame, list[str]]
        - DataFrame: ``entity_id_column`` + ``time_column`` の 2 列と
          解決済み列名を持つ Polars DataFrame。
        - list[str]: 追加された列名のリスト。

    Notes
    -----
    ``fitted_values`` は MultiIndex を持つ pandas Series で返ってくる。
    ``reset_index()`` して entity / time 列を平坦化してから
    Polars に変換し、元テーブルと 2 キー ``left_join`` する。
    """
    # standardized は linearmodels では未サポート
    _opts = DiagnosticExtractOptions(
        dep_var=options.dep_var,
        existing_cols=options.existing_cols,
        target=options.target,
        include_interval=options.include_interval,
    )
    col_map = _build_col_names(
        _opts,
        supports_interval=True,
        supports_standardized=False,
    )

    use_effects = panel_config.fe_type == "total"
    data_frames: list[pl.DataFrame] = []

    # 予測値 DataFrame の骨格を先に作成
    if "fitted" in col_map:
        try:
            fv_series = model.fitted_values(  # type: ignore[union-attr]
                effects=use_effects
            )
        except TypeError:
            # effects 引数非対応の場合のフォールバック
            fv_series = model.fitted_values  # type: ignore[union-attr]

        fv_df = fv_series.reset_index()
        # MultiIndex の level 名は通常 entity_col と time_col になる
        fv_df.columns = [
            panel_config.entity_id_column,
            panel_config.time_column,
            col_map["fitted"],
        ]
        fv_polars = pl.from_pandas(fv_df).with_columns(
            pl.col(col_map["fitted"]).cast(pl.Float64)
        )
        data_frames.append(fv_polars)

    if "resid" in col_map:
        rv_series = model.resids  # type: ignore[union-attr]
        rv_df = rv_series.reset_index()
        rv_df.columns = [
            panel_config.entity_id_column,
            panel_config.time_column,
            col_map["resid"],
        ]
        rv_polars = pl.from_pandas(rv_df).with_columns(
            pl.col(col_map["resid"]).cast(pl.Float64)
        )
        data_frames.append(rv_polars)

    # 信頼区間（summary_frame が使える場合のみ）
    if "fitted_lower_95" in col_map or "fitted_upper_95" in col_map:
        try:
            pred = model.predict()  # type: ignore[union-attr]
            sf = pred.summary_frame()
            lower_series = sf["lower_ci"].reset_index()
            upper_series = sf["upper_ci"].reset_index()
            if "fitted_lower_95" in col_map:
                lower_series.columns = [
                    panel_config.entity_id_column,
                    panel_config.time_column,
                    col_map["fitted_lower_95"],
                ]
                data_frames.append(
                    pl.from_pandas(lower_series).with_columns(
                        pl.col(col_map["fitted_lower_95"]).cast(pl.Float64)
                    )
                )
            if "fitted_upper_95" in col_map:
                upper_series.columns = [
                    panel_config.entity_id_column,
                    panel_config.time_column,
                    col_map["fitted_upper_95"],
                ]
                data_frames.append(
                    pl.from_pandas(upper_series).with_columns(
                        pl.col(col_map["fitted_upper_95"]).cast(pl.Float64)
                    )
                )
        except Exception:
            pass  # 信頼区間取得失敗時はスキップ

    if not data_frames:
        # 何も追加するものがない場合は空の DataFrame を返す
        return pl.DataFrame(), []

    # 全 DataFrame を entity_id_column + time_column で結合
    result_df = data_frames[0]
    for other_df in data_frames[1:]:
        result_df = result_df.join(
            other_df,
            on=[panel_config.entity_id_column, panel_config.time_column],
            how="left",
        )

    added_cols = list(col_map.values())
    return result_df, added_cols


# ---------------------------------------------------------------------------
# linearmodels IV（2SLS / GMM）
# ---------------------------------------------------------------------------


def extract_from_linearmodels_iv(
    model: object,
    options: DiagnosticExtractOptions,
) -> tuple[pl.DataFrame, list[str]]:
    """
    linearmodels の IV（2SLS/GMM）回帰結果から診断値を抽出する。

    Parameters
    ----------
    model:
        ``linearmodels.iv.results.IVResults`` または互換オブジェクト。
    options:
        共通の診断値抽出オプション。
        IV では standardized / include_interval は未サポート。

    Returns
    -------
    tuple[pl.DataFrame, list[str]]
        - DataFrame: ``__row_idx__`` と解決済み列名を持つ Polars DataFrame。
        - list[str]: 追加された列名のリスト。
    """
    # IV では standardized / include_interval は未サポート
    _opts = DiagnosticExtractOptions(
        dep_var=options.dep_var,
        existing_cols=options.existing_cols,
        target=options.target,
    )
    col_map = _build_col_names(
        _opts,
        supports_interval=False,
        supports_standardized=False,
    )

    # fitted_values は pandas DataFrame（shape: (n, 1)）
    # または pandas Series として返ることがある（バージョン依存）
    fv_obj = model.fitted_values  # type: ignore[union-attr]
    if hasattr(fv_obj, "squeeze"):
        # DataFrame: (n, 1) → 1D numpy 配列
        fv_arr = np.asarray(fv_obj.values.squeeze(), dtype=np.float64)
    else:
        fv_arr = np.asarray(fv_obj, dtype=np.float64)

    fv_index = fv_obj.index.to_numpy().astype(np.int64)

    data: dict[str, pl.Series] = {
        "__row_idx__": pl.Series("__row_idx__", fv_index, dtype=pl.Int64)
    }

    if "fitted" in col_map:
        data[col_map["fitted"]] = pl.Series(
            col_map["fitted"],
            fv_arr,
            dtype=pl.Float64,
        )

    if "resid" in col_map:
        resid = np.asarray(model.resids, dtype=np.float64)  # type: ignore[union-attr]
        data[col_map["resid"]] = pl.Series(
            col_map["resid"], resid, dtype=pl.Float64
        )

    df = pl.DataFrame(data)
    added_cols = list(col_map.values())
    return df, added_cols


# ---------------------------------------------------------------------------
# sklearn（Ridge / Lasso）
# ---------------------------------------------------------------------------


def extract_from_sklearn(
    reg_result: RegularizedResult,
    options: DiagnosticExtractOptions,
) -> tuple[pl.DataFrame, list[str]]:
    """
    sklearn の正則化回帰結果から診断値を抽出する。

    ``RegularizedResult.pipeline.predict(x_data)`` で予測値を再計算する。
    残差は ``y_data - predicted`` で算出する。

    標準化残差・信頼区間は正則化回帰では未サポート。

    Parameters
    ----------
    reg_result:
        ``RegularizedResult`` データクラス。
        ``pipeline``, ``x_data``, ``y_data`` が設定されている必要がある。
    options:
        共通の診断値抽出オプション。
        sklearn 正則化回帰では standardized / include_interval は未サポート。
    target:
        抽出する値の種類。

    Returns
    -------
    tuple[pl.DataFrame, list[str]]
        - DataFrame: ``__row_idx__`` と解決済み列名を持つ Polars DataFrame。
        - list[str]: 追加された列名のリスト。
    """
    col_map = _build_col_names(
        options,
        supports_interval=False,
        supports_standardized=False,
    )

    fitted_values = reg_result.pipeline.predict(reg_result.x_data).astype(
        np.float64
    )
    n = len(fitted_values)
    index = np.arange(n, dtype=np.int64)

    data: dict[str, pl.Series] = {
        "__row_idx__": pl.Series("__row_idx__", index, dtype=pl.Int64)
    }

    if "fitted" in col_map:
        data[col_map["fitted"]] = pl.Series(
            col_map["fitted"], fitted_values, dtype=pl.Float64
        )

    if "resid" in col_map:
        y = reg_result.y_data.astype(np.float64)
        resid = y - fitted_values
        data[col_map["resid"]] = pl.Series(
            col_map["resid"], resid, dtype=pl.Float64
        )

    df = pl.DataFrame(data)
    added_cols = list(col_map.values())
    return df, added_cols

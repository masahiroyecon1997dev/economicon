"""
回帰診断列の抽出ユーティリティ

推定済みモデルオブジェクト（statsmodels / linearmodels / sklearn）から
予測値・残差などの診断値を Polars DataFrame として返す純粋関数群。
"""

from typing import TYPE_CHECKING, Literal

import numpy as np
import polars as pl

if TYPE_CHECKING:
    from economicon.services.regressions.fitters import RegularizedResult


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
    existing_cols: list[str],
    dep_var: str,
    target: Literal["fitted", "residual", "both"],
    standardized: bool,
    include_interval: bool,
    supports_interval: bool = False,
    supports_standardized: bool = False,
) -> dict[str, str]:
    """
    必要な列名をまとめて解決して辞書で返す。

    返り値のキーは内部キー（"fitted", "resid" 等）、
    値は実際にテーブルに追加する列名。

    Args:
        existing_cols: 現在テーブルに存在する列名リスト
        dep_var: 被説明変数名（列名接頭辞として使用）
        target: 追加する値の種類
        standardized: 標準化残差を含めるか
        include_interval: 95%信頼区間を含めるか
        supports_interval: モデルが信頼区間をサポートするか
        supports_standardized: モデルが標準化残差をサポートするか

    Returns:
        内部キー → 解決済み列名 の辞書
    """
    resolved: dict[str, str] = {}
    # 作業用に「決定済み列名を追加した仮リスト」を用意し、
    # 同一バッチ内での衝突も回避する。
    working_cols = list(existing_cols)

    def _add(key: str, base: str) -> None:
        name = resolve_column_name(working_cols, base)
        resolved[key] = name
        working_cols.append(name)

    if target in ("fitted", "both"):
        _add("fitted", f"{dep_var}_fitted")
        if include_interval and supports_interval:
            _add("fitted_lower_95", f"{dep_var}_fitted_lower_95")
            _add("fitted_upper_95", f"{dep_var}_fitted_upper_95")

    if target in ("residual", "both"):
        _add("resid", f"{dep_var}_resid")
        if standardized and supports_standardized:
            _add("resid_std", f"{dep_var}_resid_std")

    return resolved


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
    dep_var: str,
    existing_cols: list[str],
    target: Literal["fitted", "residual", "both"],
    standardized: bool,
    include_interval: bool,
) -> tuple[pl.DataFrame, list[str]]:
    """
    statsmodels の回帰結果から診断値を抽出する。

    Parameters
    ----------
    model:
        ``statsmodels`` の ``RegressionResultsWrapper``
        （または互換の fitted result オブジェクト）。
    dep_var:
        被説明変数名。列名接頭辞として使用される。
    existing_cols:
        現在テーブルに存在する列名リスト（重複回避用）。
    target:
        抽出する値の種類。
    standardized:
        標準化残差（studentized internal）を含めるか。
    include_interval:
        予測値の 95%信頼区間を含めるか。

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
        existing_cols=existing_cols,
        dep_var=dep_var,
        target=target,
        standardized=standardized,
        include_interval=include_interval,
        supports_interval=True,
        supports_standardized=True,
    )

    # statsmodels のインデックスを行番号として使用
    # numpy 配列入力の場合は missing_row_idx から再構築する
    index = _get_statsmodels_row_indices(model)
    data: dict[str, pl.Series] = {
        "__row_idx__": pl.Series("__row_idx__", index, dtype=pl.Int64)
    }

    if "fitted" in col_map:
        fitted = np.asarray(model.fittedvalues, dtype=np.float64)  # type: ignore[union-attr]
        data[col_map["fitted"]] = pl.Series(
            col_map["fitted"], fitted, dtype=pl.Float64
        )

    if "fitted_lower_95" in col_map or "fitted_upper_95" in col_map:
        try:
            # predict() は summary_frame() が返す DataFrame を利用
            sf = model.get_prediction().summary_frame(alpha=0.05)  # type: ignore[union-attr]
            if "fitted_lower_95" in col_map:
                data[col_map["fitted_lower_95"]] = pl.Series(
                    col_map["fitted_lower_95"],
                    sf["mean_ci_lower"].to_numpy(),
                    dtype=pl.Float64,
                )
            if "fitted_upper_95" in col_map:
                data[col_map["fitted_upper_95"]] = pl.Series(
                    col_map["fitted_upper_95"],
                    sf["mean_ci_upper"].to_numpy(),
                    dtype=pl.Float64,
                )
        except Exception:
            # 信頼区間が取得できない場合（Logit/Probit 等）は None 列を追加
            n = len(index)
            if "fitted_lower_95" in col_map:
                data[col_map["fitted_lower_95"]] = pl.Series(
                    col_map["fitted_lower_95"], [None] * n, dtype=pl.Float64
                )
            if "fitted_upper_95" in col_map:
                data[col_map["fitted_upper_95"]] = pl.Series(
                    col_map["fitted_upper_95"], [None] * n, dtype=pl.Float64
                )

    if "resid" in col_map:
        resid = np.asarray(model.resid, dtype=np.float64)  # type: ignore[union-attr]
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
            n = len(index)
            data[col_map["resid_std"]] = pl.Series(
                col_map["resid_std"], [None] * n, dtype=pl.Float64
            )

    df = pl.DataFrame(data)
    added_cols = [v for k, v in col_map.items()]
    return df, added_cols


# ---------------------------------------------------------------------------
# Tobit（py4etrics）
# ---------------------------------------------------------------------------


def extract_from_tobit(
    model: object,
    dep_var: str,
    existing_cols: list[str],
    target: Literal["fitted", "residual", "both"],
) -> tuple[pl.DataFrame, list[str]]:
    """
    py4etrics の Tobit 回帰結果から診断値を抽出する。

    Tobit には ``.fittedvalues`` 属性が存在しないため、
    ``.predict()`` メソッドで予測値を求める。
    残差は ``model.endog - model.predict()`` で算出する。

    標準化残差・信頼区間は Tobit では未サポート（None 列として追加されない）。

    Parameters
    ----------
    model:
        ``py4etrics.Tobit`` の fitted result オブジェクト。
    dep_var:
        被説明変数名。列名接頭辞として使用される。
    existing_cols:
        現在テーブルに存在する列名リスト（重複回避用）。
    target:
        抽出する値の種類。

    Returns
    -------
    tuple[pl.DataFrame, list[str]]
        - DataFrame: ``__row_idx__`` と解決済み列名を持つ Polars DataFrame。
        - list[str]: 追加された列名のリスト。
    """
    col_map = _build_col_names(
        existing_cols=existing_cols,
        dep_var=dep_var,
        target=target,
        # Tobit は standardized / include_interval 未サポート
        standardized=False,
        include_interval=False,
        supports_interval=False,
        supports_standardized=False,
    )

    # py4etrics Tobit: .fittedvalues は numpy.ndarray で返る
    # .predict() は NotImplementedError を投げるため使用しない
    fitted_arr = np.asarray(model.fittedvalues, dtype=np.float64)  # type: ignore[union-attr]
    n = len(fitted_arr)
    index = np.arange(n, dtype=np.int64)

    data: dict[str, pl.Series] = {
        "__row_idx__": pl.Series("__row_idx__", index, dtype=pl.Int64)
    }

    if "fitted" in col_map:
        data[col_map["fitted"]] = pl.Series(
            col_map["fitted"], fitted_arr, dtype=pl.Float64
        )

    if "resid" in col_map:
        # .resid が利用可能（= endog - fittedvalues）
        resid = np.asarray(model.resid, dtype=np.float64)  # type: ignore[union-attr]
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
    dep_var: str,
    entity_id_column: str,
    time_column: str,
    existing_cols: list[str],
    target: Literal["fitted", "residual", "both"],
    include_interval: bool,
    fe_type: Literal["total", "within"],
) -> tuple[pl.DataFrame, list[str]]:
    """
    linearmodels のパネル回帰結果から診断値を抽出する。

    Parameters
    ----------
    model:
        ``linearmodels.panel.PanelEffectsResults``
        または ``RandomEffectsResults``。
    dep_var:
        被説明変数名。列名接頭辞として使用される。
    entity_id_column:
        エンティティ（個体）を識別する列名。結合キーとして使用。
    time_column:
        時間を識別する列名。結合キーとして使用。
    existing_cols:
        現在テーブルに存在する列名リスト（重複回避用）。
    target:
        抽出する値の種類。
    include_interval:
        予測値の 95%信頼区間を含めるか。
    fe_type:
        "total": 固定効果を含む予測（effects=True）、
        "within": 固定効果を除いた変動成分（effects=False）。

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
    col_map = _build_col_names(
        existing_cols=existing_cols,
        dep_var=dep_var,
        target=target,
        # standardized は linearmodels では未サポート
        standardized=False,
        include_interval=include_interval,
        supports_interval=True,
        supports_standardized=False,
    )

    use_effects = fe_type == "total"
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
        fv_df.columns = [entity_id_column, time_column, col_map["fitted"]]
        fv_polars = pl.from_pandas(fv_df).with_columns(
            pl.col(col_map["fitted"]).cast(pl.Float64)
        )
        data_frames.append(fv_polars)

    if "resid" in col_map:
        rv_series = model.resids  # type: ignore[union-attr]
        rv_df = rv_series.reset_index()
        rv_df.columns = [entity_id_column, time_column, col_map["resid"]]
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
                    entity_id_column,
                    time_column,
                    col_map["fitted_lower_95"],
                ]
                data_frames.append(
                    pl.from_pandas(lower_series).with_columns(
                        pl.col(col_map["fitted_lower_95"]).cast(pl.Float64)
                    )
                )
            if "fitted_upper_95" in col_map:
                upper_series.columns = [
                    entity_id_column,
                    time_column,
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
            other_df, on=[entity_id_column, time_column], how="left"
        )

    added_cols = list(col_map.values())
    return result_df, added_cols


# ---------------------------------------------------------------------------
# linearmodels IV（2SLS / GMM）
# ---------------------------------------------------------------------------


def extract_from_linearmodels_iv(
    model: object,
    dep_var: str,
    existing_cols: list[str],
    target: Literal["fitted", "residual", "both"],
    include_interval: bool,
) -> tuple[pl.DataFrame, list[str]]:
    """
    linearmodels の IV（2SLS/GMM）回帰結果から診断値を抽出する。

    Parameters
    ----------
    model:
        ``linearmodels.iv.results.IVResults`` または互換オブジェクト。
    dep_var:
        被説明変数名。列名接頭辞として使用される。
    existing_cols:
        現在テーブルに存在する列名リスト（重複回避用）。
    target:
        抽出する値の種類。
    include_interval:
        予測値の 95%信頼区間を含めるか（IV では通常非対応のためスキップ）。

    Returns
    -------
    tuple[pl.DataFrame, list[str]]
        - DataFrame: ``__row_idx__`` と解決済み列名を持つ Polars DataFrame。
        - list[str]: 追加された列名のリスト。
    """
    col_map = _build_col_names(
        existing_cols=existing_cols,
        dep_var=dep_var,
        target=target,
        # IV では standardized は未サポート
        standardized=False,
        include_interval=include_interval,
        supports_interval=False,
        supports_standardized=False,
    )

    # fitted_values は pandas DataFrame（shape: (n, 1), columns: ['fitted_values']）
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
    dep_var: str,
    existing_cols: list[str],
    target: Literal["fitted", "residual", "both"],
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
    dep_var:
        被説明変数名。列名接頭辞として使用される。
    existing_cols:
        現在テーブルに存在する列名リスト（重複回避用）。
    target:
        抽出する値の種類。

    Returns
    -------
    tuple[pl.DataFrame, list[str]]
        - DataFrame: ``__row_idx__`` と解決済み列名を持つ Polars DataFrame。
        - list[str]: 追加された列名のリスト。
    """
    col_map = _build_col_names(
        existing_cols=existing_cols,
        dep_var=dep_var,
        target=target,
        # sklearn 正則化回帰は standardized / include_interval 未サポート
        standardized=False,
        include_interval=False,
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

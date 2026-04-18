"""
DID 分析のデータ準備・推定ヘルパー関数

- データ検証（パネル一意性・basePeriod 存在確認）
- Polars で交差項列を生成し Pandas MultiIndex に変換
- PanelOLS（TWFE）の推定
- 並行トレンド Wald 検定
"""

from __future__ import annotations

import gc
from typing import TYPE_CHECKING, Any

import numpy as np
import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.entities import (
    ClusteredStandardError,
    HacStandardError,
)
from economicon.services.regressions.common import (
    LINEARMODELS_COV_TYPE_MAP,
    handle_missing_values,
)
from economicon.utils import ProcessingError

if TYPE_CHECKING:
    from economicon.schemas.entities import StandardErrorSettings

# 基本 DID 交差項の内部列名
_DID_INTERACT_COL = "_did_interact"
# Event Study 相互作用項列名のプレフィックス
_ES_PREFIX = "_es_"
_ES_PREFIX_LEN = len(_ES_PREFIX)


def _es_col(period: int) -> str:
    """Event Study 相互作用項の列名を生成する。"""
    return f"{_ES_PREFIX}{period}"


def _es_col_to_period(col_name: str) -> int | None:
    """列名から Event Study の期間値を逆引きする。"""
    if col_name.startswith(_ES_PREFIX):
        try:
            return int(col_name[_ES_PREFIX_LEN:])
        except ValueError:
            return None
    return None


def auto_select_base_period(
    df: pl.DataFrame,
    time_column: str,
    post_column: str,
) -> int:
    """
    post=0 の最大時点を basePeriod として自動選択する。

    通常、処置直前期（例: t=-1 や最終 pre-treatment 年）となる。

    Raises:
        ProcessingError: post=0 の期間が存在しない場合
    """
    val = (
        df.filter(pl.col(post_column) == 0)
        .select(pl.col(time_column).max())
        .item()
    )
    if val is None:
        raise ProcessingError(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=_(
                "No pre-treatment period found. "
                "Ensure postColumn contains at least one 0."
            ),
        )
    return int(val)


def validate_base_period_in_data(
    df: pl.DataFrame,
    time_column: str,
    base_period: int,
) -> None:
    """
    basePeriod がデータの時点集合に含まれることを検証する。

    Raises:
        ProcessingError: base_period が時点集合に含まれない場合
    """
    periods = sorted(df[time_column].unique().to_list())
    if base_period not in periods:
        raise ProcessingError(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=_(
                "basePeriod {} is not in the data."
                " Available periods: {}"
            ).format(base_period, periods),
        )


def validate_panel_uniqueness(
    df: pl.DataFrame,
    entity_id_column: str,
    time_column: str,
) -> None:
    """
    同一個体・同一時点の重複行がないことを検証する。

    非バランスパネル（観測数が個体間で異なる）は許容する。

    Raises:
        ProcessingError: 重複がある場合
    """
    has_dups: bool = (
        df.select([entity_id_column, time_column]).is_duplicated().any()
    )
    if has_dups:
        raise ProcessingError(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=_(
                "Duplicate (entity, time) pairs found in data."
                " Each combination of entityIdColumn"
                " and timeColumn must be unique."
            ),
        )


def build_interaction_columns(
    df: pl.DataFrame,
    *,
    treatment_column: str,
    post_column: str,
    time_column: str,
    include_event_study: bool,
    base_period: int,
) -> tuple[pl.DataFrame, str | None, list[str]]:
    """
    DID 交差項列を Polars DataFrame に追加する。

    基本 DID: treatment × post → `_did_interact`
    Event Study: treatment × 1[t=k] for k ≠ base_period

    Returns
    -------
    df : pl.DataFrame
        交差項列を追加した DataFrame
    interact_col : str | None
        基本 DID の交差項列名（Event Study では None）
    es_cols : list[str]
        Event Study 相互作用項列名（時間順）
    """
    if not include_event_study:
        df = df.with_columns(
            (
                pl.col(treatment_column) * pl.col(post_column)
            ).alias(_DID_INTERACT_COL)
        )
        return df, _DID_INTERACT_COL, []

    # Event Study: 各時点（base_period を除く）の交差項を生成
    periods = sorted(df[time_column].unique().to_list())
    es_cols: list[str] = []
    exprs = []
    for t in periods:
        if t == base_period:
            continue
        col_name = _es_col(t)
        exprs.append(
            (
                pl.col(treatment_column)
                * (pl.col(time_column) == t).cast(pl.Float64)
            ).alias(col_name)
        )
        es_cols.append(col_name)

    df = df.with_columns(exprs)
    return df, None, es_cols


def prepare_did_dataframe(
    df_polars: pl.DataFrame,
    *,
    dependent_variable: str,
    entity_id_column: str,
    time_column: str,
    treatment_column: str,
    x_columns: list[str],
    missing: str,
) -> Any:
    """
    DID 用の Pandas MultiIndex DataFrame を準備する。

    欠損値処理後に (entity_id, time) を MultiIndex に設定する。
    x_columns には交差項列と explanatory_variables を含める。

    Args:
        df_polars: 交差項列追加済みの Polars DataFrame
        dependent_variable: 被説明変数列名
        entity_id_column: 個体 ID 列名
        time_column: 時点列名
        treatment_column: 処置群ダミー列名（entity 統計量算出用）
        x_columns: 交差項 + 共変量の列名リスト
        missing: 欠損値処理方法 ("none" / "drop" / "raise")

    Returns:
        (entity_id, time) MultiIndex 付き Pandas DataFrame
    """
    required_cols = list(
        dict.fromkeys(
            [dependent_variable]
            + x_columns
            + [treatment_column, entity_id_column, time_column]
        )
    )
    df = df_polars.select(required_cols).to_pandas(
        use_pyarrow_extension_array=True
    )
    del df_polars
    gc.collect()

    df = handle_missing_values(df, missing)
    df = df.set_index([entity_id_column, time_column])
    return df


def resolve_cov_kwargs(
    se: StandardErrorSettings,
    entity_id_column: str,
    time_column: str,
) -> tuple[str, dict]:
    """
    StandardErrorSettings を PanelOLS の cov 引数に変換する。

    DID のクラスタ SE:
    - groups に entity_id_column → cluster_entity=True
    - groups に time_column     → cluster_time=True
    - それ以外 (groups が列名不一致) → 両方 True（フォールバック）

    Returns:
        (cov_type, extra_kwargs) のタプル
    """
    match se:
        case ClusteredStandardError():
            groups_set = set(se.groups)
            has_entity = entity_id_column in groups_set
            has_time = time_column in groups_set
            if has_entity and has_time:
                cov_kwargs: dict = {
                    "cluster_entity": True,
                    "cluster_time": True,
                }
            elif has_entity:
                cov_kwargs = {"cluster_entity": True}
            elif has_time:
                cov_kwargs = {"cluster_time": True}
            else:
                # 指定列が entity/time のどちらでもない場合は両方 True
                cov_kwargs = {
                    "cluster_entity": True,
                    "cluster_time": True,
                }
            return "clustered", cov_kwargs
        case HacStandardError():
            return "kernel", {"bandwidth": se.maxlags}
        case _:
            cov_type = LINEARMODELS_COV_TYPE_MAP.get(
                se.method, "unadjusted"
            )
            return cov_type, {}


def fit_twfe(
    df_pandas: Any,
    *,
    dependent_variable: str,
    x_columns: list[str],
    cov_type: str,
    cov_kwargs: dict,
) -> Any:
    """
    Two-Way Fixed Effects PanelOLS を推定する。

    entity_effects=True / time_effects=True を固定。
    FE モデルでは個体・時点効果が切片を吸収するため、
    定数項は追加しない。

    Eco-Note:
        linearmodels の PanelOLS は within 変換（demean）を
        用いて個体・時点固定効果を除去する。
        交差項 (D_i × P_t) の係数が ATT の一致推定量となる。

    Args:
        df_pandas: MultiIndex(entity, time) 付き Pandas DataFrame
        dependent_variable: 被説明変数列名
        x_columns: 交差項 + 共変量の列名リスト
        cov_type: linearmodels の cov_type 文字列
        cov_kwargs: fit() に追加で渡す引数辞書

    Returns:
        linearmodels の PanelOLS 結果オブジェクト
    """
    from linearmodels.panel import PanelOLS  # noqa: PLC0415

    y = df_pandas[dependent_variable]
    x = df_pandas[x_columns]
    model = PanelOLS(
        y, x, entity_effects=True, time_effects=True
    )
    return model.fit(cov_type=cov_type, **cov_kwargs)


def compute_pretrend_wald(
    model_result: Any,
    *,
    es_cols: list[str],
    base_period: int,
) -> dict | None:
    """
    Event Study の処置前係数に対する Wald F 検定を実行する。

    H0: δ_k = 0 for all k < base_period.
    処置前係数が同時にゼロであることを検定する。
    非有意（p > 0.05）が並行トレンド仮定を支持する。

    Eco-Note:
        制約行列 R を用いた Wald 検定: W = β̂ᵀ(RVRᵀ)⁻¹β̂。
        linearmodels の wald_test() を使用。

    Returns:
        検定結果の dict、または処置前期間がない場合は None
    """
    pre_cols = [
        col
        for col in es_cols
        if (p := _es_col_to_period(col)) is not None
        and p < base_period
    ]
    if not pre_cols:
        return None

    params_index = list(model_result.params.index)
    try:
        pre_idxs = [params_index.index(c) for c in pre_cols]
    except ValueError:
        return None

    n_params = len(params_index)
    r_matrix = np.zeros((len(pre_idxs), n_params))
    for row_i, col_idx in enumerate(pre_idxs):
        r_matrix[row_i, col_idx] = 1.0

    try:
        wald = model_result.wald_test(restriction=r_matrix)
        f_stat = float(wald.stat)
        p_value = float(wald.pval)
        df1 = len(pre_cols)
        df2 = int(model_result.df_resid)
    except Exception:  # linearmodels API の差異を吸収
        return None

    return {
        "fStatistic": f_stat,
        "df1": df1,
        "df2": df2,
        "pValue": p_value,
        "description": (
            "Test for parallel trends assumption"
            " (Wald test on pre-period coefficients)."
            " Non-significant p-value supports parallel"
            " trends."
        ),
    }

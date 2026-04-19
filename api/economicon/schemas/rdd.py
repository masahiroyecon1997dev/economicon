"""回帰不連続デザイン（RDD）分析関連のスキーマ定義"""

from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator, Field, model_validator

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import BaseRequest, BaseResult
from economicon.schemas.enums import (
    RDDBandwidthSelectType,
    RDDKernelType,
    RDDVceType,
)
from economicon.schemas.types import (
    ColumnName,
    ResultDescription,
    ResultName,
    TableName,
)

# ---------------------------------------------------------------------------
# BeforeValidator ヘルパー
# ---------------------------------------------------------------------------


def _coerce_kernel(v: object) -> RDDKernelType:
    """文字列を RDDKernelType に変換する（strict モード対応）"""
    if isinstance(v, str):
        return RDDKernelType(v)
    return v  # type: ignore[return-value]


def _coerce_bw_select(v: object) -> RDDBandwidthSelectType:
    """文字列を RDDBandwidthSelectType に変換する（strict モード対応）"""
    if isinstance(v, str):
        return RDDBandwidthSelectType(v)
    return v  # type: ignore[return-value]


def _coerce_vce(v: object) -> RDDVceType:
    """文字列を RDDVceType に変換する（strict モード対応）"""
    if isinstance(v, str):
        return RDDVceType(v)
    return v  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# リクエストボディ
# ---------------------------------------------------------------------------


class RDDRequestBody(BaseRequest):
    """
    回帰不連続デザイン（RDD）分析リクエスト

    rdrobust を使用したシャープ RDD 推定と診断を実行します。
    バイアス補正済み推定・密度検定・プラシーボ検定を包括的に返します。
    """

    table_name: Annotated[
        TableName,
        Field(
            description=(
                "分析対象のテーブル名。"
                "ワークスペース内に存在するテーブル名を指定してください。"
            ),
        ),
    ]
    result_name: ResultName
    description: ResultDescription
    outcome_variable: Annotated[
        ColumnName,
        Field(
            description=(
                "結果変数（y）の列名。数値型カラムを指定してください。"
            ),
        ),
    ]
    running_variable: Annotated[
        ColumnName,
        Field(
            description=(
                "実行変数（score / forcing variable）の列名。"
                "カットオフ前後で処置割り当てが決まる連続変数。"
                "数値型カラムを指定してください。"
            ),
        ),
    ]
    cutoff: Annotated[
        float,
        Field(
            default=0.0,
            description=(
                "カットオフ値。実行変数がこの値以上の観測を処置群とみなします。"
                "デフォルトは 0。"
            ),
        ),
    ]
    kernel: Annotated[
        RDDKernelType,
        BeforeValidator(_coerce_kernel),
        Field(
            default=RDDKernelType.TRIANGULAR,
            description=(
                "カーネル重み付け関数。"
                "triangular（デフォルト）/ epanechnikov / uniform。"
            ),
        ),
    ]
    bw_select: Annotated[
        RDDBandwidthSelectType,
        BeforeValidator(_coerce_bw_select),
        Field(
            default=RDDBandwidthSelectType.MSERD,
            alias="bwSelect",
            description=(
                "バンド幅の自動選定アルゴリズム。"
                "mserd（デフォルト）: MSE 最小化・左右共通バンド幅。"
                "msetwo: MSE 最小化・左右独立バンド幅。"
                "cerrd/certwo: CER（Coverage Error Rate）最小化。"
            ),
        ),
    ]
    h: Annotated[
        float | None,
        Field(
            default=None,
            gt=0.0,
            description=(
                "手動バンド幅。指定した場合 bwSelect による"
                "自動選択より優先されます。"
                "null の場合は bwSelect で自動選択します。"
            ),
        ),
    ]
    p: Annotated[
        int,
        Field(
            default=1,
            ge=1,
            le=4,
            description=(
                "局所多項式の次数、1（線形、デフォルト）または"
                "2（2次式）を推奨。"
                "バイアス補正バンド幅には p+1 次多項式が使用されます。"
            ),
        ),
    ]
    vce: Annotated[
        RDDVceType,
        BeforeValidator(_coerce_vce),
        Field(
            default=RDDVceType.HC1,
            description=(
                "分散共分散行列の推定方式（標準誤差の計算方法）。"
                "nn: 最近傍法（デフォルト）。"
                "hc1 / hc3: HC 不均一分散一致推定量。"
                "cluster: クラスタ標準誤差。"
                "nncluster: 最近傍クラスタ標準誤差。"
            ),
        ),
    ]
    confidence_level: Annotated[
        float,
        Field(
            default=0.95,
            alias="confidenceLevel",
            ge=0.5,
            le=0.999,
            description="信頼区間の水準（デフォルト: 0.95 → 95%）",
        ),
    ]
    n_bins: Annotated[
        int,
        Field(
            default=30,
            alias="nBins",
            ge=10,
            le=200,
            description=(
                "散布図用ビン数（左右合計）。デフォルト: 30（左右各 15 本）。"
            ),
        ),
    ]
    placebo_cutoffs: Annotated[
        list[float] | None,
        Field(
            default=None,
            alias="placeboCutoffs",
            max_length=10,
            description=(
                "プラシーボ検定用の偽境界値リスト。"
                "null の場合は実行変数の範囲に基づき"
                "カットオフ左右 ±5% 相当の 2 点を自動生成します。"
            ),
        ),
    ]

    @model_validator(mode="after")
    def _validate_placebo_cutoffs(self) -> RDDRequestBody:
        """プラシーボ境界値が本来のカットオフと重複しないことを検証する。"""
        if self.placebo_cutoffs is None:
            return self
        if self.cutoff in self.placebo_cutoffs:
            raise ValueError(
                _("placeboCutoffs must not contain the main cutoff value.")
            )
        return self


# ---------------------------------------------------------------------------
# RDD 分析実行レスポンス
# ---------------------------------------------------------------------------


class RDDResult(BaseResult):
    """RDD 分析実行レスポンス"""

    result_id: str = Field(
        title="Result ID",
        description="保存された分析結果の一意 ID",
    )


# ---------------------------------------------------------------------------
# 分析結果データ構造（result_store に格納される詳細データ）
# ---------------------------------------------------------------------------


class RDDEstimate(BaseResult):
    """
    RDD 推定量（LATE: Local Average Treatment Effect）

    カットオフにおける結果変数の不連続の大きさ。
    rdrobust は conventional / bias-corrected / robust の
    3 種類の推定値を出力する。
    """

    # Eco-Note: rdrobust の conventional 推定量は局所多項式 p 次の係数。
    #   バイアス補正推定量はバイアス項を推定し点推定値を補正したもの。
    #   信頼区間は robust CI（bias-corrected 点推定 + robust SE）を推奨。
    coef: float = Field(
        description="推定された不連続の大きさ（conventional 推定値）"
    )
    std_err: float = Field(description="標準誤差（conventional）")
    z_stat: float = Field(description="z 統計量（conventional）")
    p_value: float = Field(description="p 値（conventional）")
    ci_lower: float = Field(description="信頼区間下限（conventional）")
    ci_upper: float = Field(description="信頼区間上限（conventional）")
    bias_corrected_coef: float = Field(
        description="バイアス補正後の推定値（bias-corrected）"
    )
    bias_corrected_ci_lower: float = Field(
        description="バイアス補正済みロバスト信頼区間下限"
    )
    bias_corrected_ci_upper: float = Field(
        description="バイアス補正済みロバスト信頼区間上限"
    )
    rho: float = Field(
        description=(
            "バンド幅比率 h/b。"
            "バイアスと分散のトレードオフを示す指標。"
            "値が大きいほどバイアス補正が弱くなる。"
        )
    )


class RDDBandwidth(BaseResult):
    """バンド幅とサンプル数情報"""

    bw_left: float = Field(description="カットオフ左側のメインバンド幅 h")
    bw_right: float = Field(description="カットオフ右側のメインバンド幅 h")
    bw_bias_left: float = Field(
        description="カットオフ左側のバイアス補正バンド幅 b"
    )
    bw_bias_right: float = Field(
        description="カットオフ右側のバイアス補正バンド幅 b"
    )
    n_left: int = Field(
        description="左側のバンド幅内有効サンプル数（推定に寄与）"
    )
    n_right: int = Field(
        description="右側のバンド幅内有効サンプル数（推定に寄与）"
    )
    n_total: int = Field(description="全サンプル数")


class RDDBinPoint(BaseResult):
    """散布図用ビンデータの 1 点"""

    x: float = Field(description="ビン内の実行変数平均値")
    y: float = Field(description="ビン内の結果変数平均値")


class RDDPolyFitSide(BaseResult):
    """左右いずれか一方の多項式フィット曲線データ"""

    x: list[float] = Field(description="グリッド点の実行変数値（100 点）")
    y: list[float] = Field(description="対応する多項式フィット値")


class RDDPolyFitData(BaseResult):
    """局所多項式フィット曲線（左右それぞれ）"""

    left: RDDPolyFitSide = Field(description="カットオフ左側フィット曲線")
    right: RDDPolyFitSide = Field(description="カットオフ右側フィット曲線")


class RDDDensityTest(BaseResult):
    """
    McCrary 密度検定（rddensity による）

    帰無仮説 H0: カットオフにおいて実行変数の密度は連続
    非有意（p > 0.05）が操作なし（RDD の妥当性）を支持する。
    """

    test_statistic: float = Field(
        description="密度不連続検定統計量（T 統計量）"
    )
    p_value: float = Field(description="p 値")
    description: str = Field(
        description=(
            "検定結果の解釈文。"
            "例: 'Non-significant p-value supports no manipulation.'"
        )
    )


class RDDPlaceboTest(BaseResult):
    """
    プラシーボ検定結果（偽の境界値でのRDD推定）

    本来の境界以外でも有意な不連続が現れる場合、
    識別戦略の妥当性に問題がある可能性を示す。
    """

    cutoff: float = Field(description="プラシーボ境界値")
    coef: float = Field(description="プラシーボ境界での推定値")
    std_err: float = Field(description="標準誤差")
    p_value: float = Field(description="p 値（conventional）")
    ci_lower: float = Field(description="信頼区間下限")
    ci_upper: float = Field(description="信頼区間上限")
    is_significant: bool = Field(
        description=(
            "5% 水準で有意かどうか。True = RDD の妥当性に問題がある可能性。"
        )
    )


class RDDResultData(BaseResult):
    """
    RDD 分析結果の詳細データ

    analysis_result_store に result_data として格納される。
    GET /analysis/results/{id} で取得可能。
    """

    table_name: str = Field(description="分析対象テーブル名")
    outcome_variable: str = Field(description="結果変数名")
    running_variable: str = Field(description="実行変数名")
    cutoff: float = Field(description="カットオフ値")
    kernel: str = Field(description="使用したカーネル関数")
    p: int = Field(description="多項式次数")
    vce: str = Field(description="分散推定方式")
    confidence_level: float = Field(description="信頼区間の水準")
    estimate: RDDEstimate = Field(description="推定統計値")
    bandwidth: RDDBandwidth = Field(description="バンド幅とサンプル情報")
    bins_data: list[RDDBinPoint] = Field(
        description=(
            "散布図用ビンデータ。実行変数を等幅ビンに分割した際の"
            "各ビン中央の x 値と y 平均値。"
        )
    )
    poly_fit_data: RDDPolyFitData = Field(
        description=(
            "局所多項式フィット曲線。カットオフ左右それぞれのグリッド点座標。"
        )
    )
    density_test: RDDDensityTest | None = Field(
        default=None,
        description=("McCrary 密度検定結果（rddensity による操作検定）。"),
    )
    placebo_tests: list[RDDPlaceboTest] = Field(
        description=(
            "プラシーボ検定結果。"
            "偽の境界値での推定が有意でないことを確認する。"
        )
    )

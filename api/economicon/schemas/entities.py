from typing import Annotated, Literal

from pydantic import Field

from economicon.schemas.common import BaseRequest, BinaryChoiceRegularization
from economicon.schemas.enums import (
    RegressionMethodType,
    StandardErrorMethodType,
)
from economicon.schemas.types import (
    ColumnName,
    DistributionConfig,
    NewColumnName,
)


class SimulationColumnConfig(BaseRequest):
    """
    新しい列名とその生成規則のペア。
    複数のAPI（列追加、シミュレーション設定等）で共通利用される。
    """

    column_name: NewColumnName
    distribution: DistributionConfig


class SortInstruction(BaseRequest):
    column_name: ColumnName
    ascending: bool


class OLSParams(BaseRequest):
    method: Literal[RegressionMethodType.OLS]


class RegularizedRegressionParams(BaseRequest):
    method: Literal[RegressionMethodType.LASSO, RegressionMethodType.RIDGE]
    # 正則化のパラメータalphaを追加
    alpha: float = Field(
        default=1.0, ge=0.0, description="正則化強度のパラメータ"
    )
    # Eco-Note D: alpha_convention により alpha の解釈が変わる。
    # "glmnet" (デフォルト): R の glmnet パッケージの λ に相当。
    #   Lasso: 1/n*||y-Xβ||² + λ*||β||₁  → statsmodels α = λ/2
    #   Ridge: 1/n*||y-Xβ||² + λ*||β||²  → statsmodels α = λ
    # "sklearn": scikit-learn の alpha に相当。
    #   Lasso: statsmodels α = α_sk (同一式)
    #   Ridge: statsmodels α = α_sk / n (n はサンプル数)
    alpha_convention: Literal["glmnet", "sklearn"] = Field(
        default="glmnet",
        alias="alphaConvention",
        description=(
            "alpha の規約。"
            "'glmnet': R の glmnet パッケージ準拠"
            "（計量経済学・統計学のデフォルト）。"
            "'sklearn': scikit-learn 準拠。"
        ),
    )
    max_iter: int = Field(
        default=1000,
        ge=1,
        le=100000,
        alias="maxIter",
        description="座標降下法の最大反復回数。"
        "収束しない場合は増やしてください。",
    )
    calculate_se: bool = Field(
        default=False,
        alias="calculateSe",
        description="ブートストラップ法による標準誤差を計算するかどうか",
    )
    bootstrap_iterations: int = Field(
        default=1000,
        ge=100,
        le=10000,
        alias="bootstrapIterations",
        description="ブートストラップ法のイテレーション回数",
    )  # Eco-Note C: 在様固定。None 指定時は推定のたびに結果が変わる
    random_state: int | None = Field(
        default=None,
        alias="randomState",
        description="ブートストラップの乱数シード。None の場合は固定しない。"
        "実験の再現性を確保する場合は整数値を指定する。",
    )


class BinaryChoiceRegressionParams(BaseRequest):
    method: Literal[RegressionMethodType.LOGIT, RegressionMethodType.PROBIT]
    # 正則化のパラメータを追加
    regularization: BinaryChoiceRegularization | None = None
    # 平均限界効果(AME)を計算するかどうかのフラグを追加
    calculate_marginal_effects: bool = Field(
        default=False,
        alias="calculateMarginalEffects",
        description="平均限界効果(AME)を計算するかどうか",
    )
    # Eco-Note A: Logit/Probit の残差種別
    # raw: 生残差 (y - p̂)、deviance: デビアンス残差
    binary_residual_type: Literal["raw", "deviance"] = Field(
        default="raw",
        alias="binaryResidualType",
        description="残差種別。"
        "raw: 生残差 (y - p̂)、"
        "deviance: デビアンス残差。Logit/Probit のみ有効。",
    )


class TobitParams(BaseRequest):
    method: Literal[RegressionMethodType.TOBIT]
    # 打ち切り値を追加
    left_censoring_limit: float | None = Field(
        default=0.0,
        description="左側打ち切り値。この値以下のデータが打ち切られていると見なす",
    )
    right_censoring_limit: float | None = Field(
        default=None, description="右側打ち切り値"
    )


class InstrumentalVariablesParams(BaseRequest):
    method: Literal[RegressionMethodType.IV]
    iv_method: Literal["2sls", "gmm"] = Field(
        default="2sls",
        description="推定アルゴリズム。過剰識別かつ異分散がある場合はGMMを推奨",
    )
    # 操作変数と内生変数の列名リストを追加
    instrumental_variables: list[ColumnName]
    endogenous_variables: list[ColumnName]
    # GMMを選択した場合の重み行列の設定（必要なら）
    gmm_weight_matrix: Literal["uncentered", "robust", "hac"] = "robust"


class PanelDataParams(BaseRequest):
    method: Literal[RegressionMethodType.FE, RegressionMethodType.RE]
    # 個体ID列と時間列を追加
    entity_id_column: ColumnName = Field(description="個体ID列名")
    time_column: ColumnName | None = Field(
        default=None, description="時間列名"
    )


class PanelIvParams(BaseRequest):
    method: Literal[RegressionMethodType.FEIV]
    # 個体ID列と時間列を追加
    entity_id_column: ColumnName = Field(description="個体ID列名")
    time_column: ColumnName | None = Field(
        default=None, description="時間列名"
    )
    # 操作変数と内生変数の列名リストを追加
    instrumental_variables: list[ColumnName]
    endogenous_variables: list[ColumnName]
    # GMMを選択した場合の重み行列の設定（必要なら）
    gmm_weight_matrix: Literal["uncentered", "robust", "hac"] = "robust"


type RegressionParams = Annotated[
    OLSParams
    | RegularizedRegressionParams
    | BinaryChoiceRegressionParams
    | InstrumentalVariablesParams
    | PanelDataParams
    | TobitParams
    | PanelIvParams,
    Field(discriminator="method"),
]


class NonRobustStandardError(BaseRequest):
    method: Literal[StandardErrorMethodType.NONROBUST] = (
        StandardErrorMethodType.NONROBUST
    )


class RobustStandardError(BaseRequest):
    method: Literal[StandardErrorMethodType.ROBUST] = (
        StandardErrorMethodType.ROBUST
    )
    hc_type: Literal["HC0", "HC1", "HC2", "HC3"] = Field(default="HC1")


# --- 3. クラスター標準誤差 (Clustered) ---
class ClusteredStandardError(BaseRequest):
    method: Literal[StandardErrorMethodType.CLUSTER] = (
        StandardErrorMethodType.CLUSTER
    )
    # 必須：クラスターを形成する列名（複数指定可能なようリスト形式）
    groups: list[ColumnName] = Field(description="クラスターを構成する列名")
    use_correction: bool = Field(
        default=True, description="小標本補正を行うか"
    )


# --- 4. 自己相関・異分散低減 (HAC: Newey-West) ---
class HacStandardError(BaseRequest):
    method: Literal[StandardErrorMethodType.HAC] = StandardErrorMethodType.HAC
    # 必須：ラグの長さ
    maxlags: int = Field(..., ge=0, description="考慮する最大ラグ数")
    # オプション
    kernel: str = Field(default="bartlett", description="カーネルの種類")
    use_correction: bool = Field(
        default=True, description="小標本補正を行うか"
    )


type StandardErrorSettings = Annotated[
    NonRobustStandardError
    | RobustStandardError
    | ClusteredStandardError
    | HacStandardError,
    Field(discriminator="method"),
]

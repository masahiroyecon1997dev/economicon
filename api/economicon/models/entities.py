from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from economicon.models.common import BaseRequest, BinaryChoiceRegularization
from economicon.models.enums import (
    RegressionMethodType,
    StandardErrorMethodType,
)
from economicon.models.types import (
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


class SortInstruction(BaseModel):
    column_name: ColumnName
    ascending: bool


class OLSParams(BaseModel):
    method: Literal[RegressionMethodType.OLS]


class RegularizedRegressionParams(BaseModel):
    method: Literal[RegressionMethodType.LASSO, RegressionMethodType.RIDGE]
    # 正則化のパラメータalphaを追加
    alpha: float = Field(
        default=1.0, ge=0.0, description="正則化強度のパラメータ"
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
    )


class BinaryChoiceRegressionParams(BaseModel):
    method: Literal[RegressionMethodType.LOGIT, RegressionMethodType.PROBIT]
    # 正則化のパラメータを追加
    regularization: BinaryChoiceRegularization | None = None
    # 平均限界効果(AME)を計算するかどうかのフラグを追加
    calculate_marginal_effects: bool = Field(
        default=False,
        alias="calculateMarginalEffects",
        description="平均限界効果(AME)を計算するかどうか",
    )


class TobitParams(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    method: Literal[RegressionMethodType.TOBIT]
    # 打ち切り値を追加
    left_censoring_limit: float | None = Field(
        default=0.0,
        description="左側打ち切り値。この値以下のデータが打ち切られていると見なす",
    )
    right_censoring_limit: float | None = Field(
        default=None, description="右側打ち切り値"
    )


class InstrumentalVariablesParams(BaseModel):
    method: Literal[RegressionMethodType.IV, RegressionMethodType.FEIV]
    iv_method: Literal["2sls", "gmm"] = Field(
        default="2sls",
        description="推定アルゴリズム。過剰識別かつ異分散がある場合はGMMを推奨",
    )
    # 操作変数と内生変数の列名リストを追加
    instrumental_variables: list[ColumnName]
    endogenous_variables: list[ColumnName]
    # GMMを選択した場合の重み行列の設定（必要なら）
    gmm_weight_matrix: Literal["uncentered", "robust", "hac"] = "robust"


class PanelDataParams(BaseModel):
    method: Literal[RegressionMethodType.FE, RegressionMethodType.RE]
    # 個体ID列と時間列を追加
    entity_id_column: ColumnName = Field(description="個体ID列名")
    time_column: ColumnName | None = Field(
        default=None, description="時間列名"
    )


type RegressionParams = Annotated[
    OLSParams
    | RegularizedRegressionParams
    | BinaryChoiceRegressionParams
    | InstrumentalVariablesParams
    | PanelDataParams
    | TobitParams,
    Field(discriminator="method"),
]


class NonRobustStandardError(BaseModel):
    method: Literal[StandardErrorMethodType.NONROBUST] = (
        StandardErrorMethodType.NONROBUST
    )


class RobustStandardError(BaseModel):
    method: Literal[StandardErrorMethodType.ROBUST] = (
        StandardErrorMethodType.ROBUST
    )
    hc_type: Literal["HC0", "HC1", "HC2", "HC3"] = Field(default="HC1")


# --- 3. クラスター標準誤差 (Clustered) ---
class ClusteredStandardError(BaseModel):
    method: Literal[StandardErrorMethodType.CLUSTER] = (
        StandardErrorMethodType.CLUSTER
    )
    # 必須：クラスターを形成する列名（複数指定可能なようリスト形式）
    groups: list[ColumnName] = Field(description="クラスターを構成する列名")
    use_correction: bool = Field(
        default=True, description="小標本補正を行うか"
    )


# --- 4. 自己相関・異分散低減 (HAC: Newey-West) ---
class HacStandardError(BaseModel):
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

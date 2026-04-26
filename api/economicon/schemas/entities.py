from typing import Annotated, Literal

from pydantic import Field, model_validator

from economicon.schemas.common import BaseRequest
from economicon.schemas.enums import (
    RegressionMethodType,
    StandardErrorMethodType,
)
from economicon.schemas.types import (
    ColumnName,
    DistributionConfig,
    NewColumnName,
    TableName,
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


class BinaryChoiceRegularization(BaseRequest):
    type: Literal["l1", "l2"] = "l1"
    alpha: float = Field(default=1.0, ge=0.0)


class OLSParams(BaseRequest):
    method: Literal[RegressionMethodType.OLS]


class _RegularizedBase(BaseRequest):
    """Lasso/Ridge 共通フィールド（内部基底クラス）"""

    # Eco-Note D: alpha_convention により alpha の解釈が変わる。
    # "glmnet" (デフォルト): R の glmnet パッケージの λ に相当。
    #   Lasso: 1/n*||y-Xβ||² + λ*||β||₁  → statsmodels α = λ/2
    #   Ridge: 1/n*||y-Xβ||² + λ*||β||²  → statsmodels α = λ
    # "sklearn": scikit-learn の alpha に相当。
    #   Lasso: statsmodels α = α_sk (同一式)
    #   Ridge: statsmodels α = α_sk / n (n はサンプル数)
    alpha: float = Field(
        default=1.0, ge=0.0, description="正則化強度のパラメータ"
    )
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
        description="座標降下法の最大反復回数。収束しない場合は増やしてください。",
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
    # Eco-Note C: 乱数固定。None 指定時は推定のたびに結果が変わる
    random_state: int | None = Field(
        default=None,
        alias="randomState",
        description="ブートストラップの乱数シード。None の場合は固定しない。",
    )


class LassoParams(_RegularizedBase):
    method: Literal[RegressionMethodType.LASSO] = RegressionMethodType.LASSO


class RidgeParams(_RegularizedBase):
    method: Literal[RegressionMethodType.RIDGE] = RegressionMethodType.RIDGE


class _BinaryChoiceBase(BaseRequest):
    """Logit/Probit 共通フィールド（内部基底クラス）"""

    regularization: BinaryChoiceRegularization | None = None
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
        description="残差種別。raw: 生残差 (y - p̂)、"
        "deviance: デビアンス残差。",
    )


class LogitParams(_BinaryChoiceBase):
    method: Literal[RegressionMethodType.LOGIT] = RegressionMethodType.LOGIT


class ProbitParams(_BinaryChoiceBase):
    method: Literal[RegressionMethodType.PROBIT] = RegressionMethodType.PROBIT


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


class _PanelBase(BaseRequest):
    """FE/RE 共通フィールド（内部基底クラス）"""

    entity_id_column: ColumnName = Field(description="個体ID列名")
    time_column: ColumnName | None = Field(
        default=None, description="時間列名"
    )


class FEParams(_PanelBase):
    method: Literal[RegressionMethodType.FE] = RegressionMethodType.FE


class REParams(_PanelBase):
    method: Literal[RegressionMethodType.RE] = RegressionMethodType.RE


class PanelIvParams(BaseRequest):
    method: Literal[RegressionMethodType.FEIV] = RegressionMethodType.FEIV
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

    @model_validator(mode="after")
    def check_identification(self) -> PanelIvParams:
        """識別条件: 操作変数の数 >= 内生変数の数。"""
        if len(self.instrumental_variables) < len(self.endogenous_variables):
            n_iv = len(self.instrumental_variables)
            n_en = len(self.endogenous_variables)
            raise ValueError(
                f"Number of instrumental variables ({n_iv})"
                f" must be >= endogenous variables ({n_en})."
            )
        return self


class WLSParams(BaseRequest):
    method: Literal[RegressionMethodType.WLS] = RegressionMethodType.WLS
    # Eco-Note: weights は 1/σ²_i に対応する列。全値が正 (> 0) であること。
    # statsmodels は WLS(y, X, weights=w) として受け取るため、
    # ユーザーが指定する列がそのまま重みとして使われる。
    weights_column: ColumnName = Field(
        description=(
            "観測値ごとの重み (1/σ²ᵢ) を格納した列名。"
            "正の数値型列が必要（全値 > 0）。"
        )
    )


class GLSParams(BaseRequest):
    method: Literal[RegressionMethodType.GLS] = RegressionMethodType.GLS
    # Eco-Note: sigma は n×n の分散共分散行列。
    # sm.GLS(y, X, sigma=Σ) の Σ として使われる。
    # テーブルの行数・列数が推定サンプル数 n と一致する必要がある。
    # GLS 使用時は欠損値処理を "error" 固定にしてサンプル数を確定させること。
    sigma_table_name: TableName = Field(
        description=(
            "n×n 正定値分散共分散行列を格納したテーブル名。"
            "分析テーブルの行数と次元が一致する正方行列が必要。"
            "GLS 使用時は欠損値処理が 'error' 固定となる。"
        )
    )


class FGLSParams(BaseRequest):
    method: Literal[RegressionMethodType.FGLS] = RegressionMethodType.FGLS
    # Eco-Note: FGLS の推定手法
    # "heteroskedastic" (デフォルト): OLS 残差 ê_i を用いて
    #   分散を推定し WLS を適用（1ステップ FGLS）。
    #   σ̂²_i = ê²_i として weights = 1/σ̂²_i。
    # "ar1": sm.GLSAR(rho=1).iterative_fit() による AR(1) 誤差構造の FGLS。
    #   時系列データで誤差が AR(1) 過程に従う場合に使用する。
    fgls_method: Literal["heteroskedastic", "ar1"] = Field(
        default="heteroskedastic",
        alias="fglsMethod",
        description=(
            "FGLS の推定手法。"
            "'heteroskedastic': OLS残差を用いた"
            "1ステップFGLS（不均一分散対応）。"
            "'ar1': AR(1)誤差構造を仮定した反復FGLS（GLSAR）。"
        ),
    )
    max_iter: int = Field(
        default=10,
        ge=1,
        le=100,
        alias="maxIter",
        description=(
            "ar1 選択時の収束判定イテレーション上限。"
            "heteroskedastic 選択時は無視される。"
        ),
    )


type RegressionParams = Annotated[
    OLSParams
    | LassoParams
    | RidgeParams
    | LogitParams
    | ProbitParams
    | InstrumentalVariablesParams
    | FEParams
    | REParams
    | TobitParams
    | PanelIvParams
    | WLSParams
    | GLSParams
    | FGLSParams,
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

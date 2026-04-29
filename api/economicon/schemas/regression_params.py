"""回帰手法パラメータ関連のスキーマ定義。"""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from economicon.schemas.common import BaseRequest
from economicon.schemas.enums import RegressionMethodType
from economicon.schemas.types import ColumnName, TableName


class BinaryChoiceRegularization(BaseRequest):
    type: Literal["l1", "l2"] = "l1"
    alpha: float = Field(default=1.0, ge=0.0)


class OLSParams(BaseRequest):
    method: Literal[RegressionMethodType.OLS]


class _RegularizedBase(BaseRequest):
    """Lasso/Ridge 共通フィールド（内部基底クラス）"""

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
    binary_residual_type: Literal["raw", "deviance"] = Field(
        default="raw",
        alias="binaryResidualType",
        description=(
            "残差種別。raw: 生残差 (y - p̂)、"
            "deviance: デビアンス残差。"
        ),
    )


class LogitParams(_BinaryChoiceBase):
    method: Literal[RegressionMethodType.LOGIT] = RegressionMethodType.LOGIT


class ProbitParams(_BinaryChoiceBase):
    method: Literal[RegressionMethodType.PROBIT] = RegressionMethodType.PROBIT


class TobitParams(BaseRequest):
    method: Literal[RegressionMethodType.TOBIT]
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
    instrumental_variables: list[ColumnName] = Field(min_length=1)
    endogenous_variables: list[ColumnName] = Field(min_length=1)
    gmm_weight_matrix: Literal["uncentered", "robust", "hac"] = "robust"

    @model_validator(mode="after")
    def check_identification(self) -> InstrumentalVariablesParams:
        if len(self.instrumental_variables) < len(self.endogenous_variables):
            n_iv = len(self.instrumental_variables)
            n_en = len(self.endogenous_variables)
            raise ValueError(
                f"Number of instrumental variables ({n_iv})"
                f" must be >= endogenous variables ({n_en})."
            )
        return self


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
    entity_id_column: ColumnName = Field(description="個体ID列名")
    time_column: ColumnName | None = Field(
        default=None, description="時間列名"
    )
    instrumental_variables: list[ColumnName]
    endogenous_variables: list[ColumnName]
    gmm_weight_matrix: Literal["uncentered", "robust", "hac"] = "robust"

    @model_validator(mode="after")
    def check_identification(self) -> PanelIvParams:
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
    weights_column: ColumnName = Field(
        description=(
            "観測値ごとの重み (1/σ²ᵢ) を格納した列名。"
            "正の数値型列が必要（全値 > 0）。"
        )
    )


class GLSParams(BaseRequest):
    method: Literal[RegressionMethodType.GLS] = RegressionMethodType.GLS
    sigma_table_name: TableName = Field(
        description=(
            "n×n 正定値分散共分散行列を格納したテーブル名。"
            "分析テーブルの行数と次元が一致する正方行列が必要。"
            "GLS 使用時は欠損値処理が 'error' 固定となる。"
        )
    )


class FGLSParams(BaseRequest):
    method: Literal[RegressionMethodType.FGLS] = RegressionMethodType.FGLS
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


__all__ = [
    "BinaryChoiceRegularization",
    "OLSParams",
    "LassoParams",
    "RidgeParams",
    "LogitParams",
    "ProbitParams",
    "TobitParams",
    "InstrumentalVariablesParams",
    "FEParams",
    "REParams",
    "PanelIvParams",
    "WLSParams",
    "GLSParams",
    "FGLSParams",
    "RegressionParams",
]

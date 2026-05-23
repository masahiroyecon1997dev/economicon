"""シミュレーション関連のスキーマ定義"""

from typing import Annotated, Literal

from pydantic import Field, field_validator

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import BaseRequest, BaseResult

# ---------------------------------------------------------------------------
# 共通ネスト型
# ---------------------------------------------------------------------------


class XDistributionParams(BaseRequest):
    """説明変数 x の母集団分布パラメータ"""

    x_mean: Annotated[
        float,
        Field(
            ge=-10,
            le=10,
            title="X Mean",
            description="説明変数 x の母平均",
        ),
    ] = 0.0
    x_variance: Annotated[
        float,
        Field(
            ge=0.1,
            le=10,
            title="X Variance",
            description="説明変数 x の母分散",
        ),
    ] = 1.0


# ---------------------------------------------------------------------------
# 信頼区間シミュレーション
# ---------------------------------------------------------------------------


class ConfidenceIntervalSimRequestBody(BaseRequest):
    """信頼区間シミュレーションリクエスト"""

    ci_type: Literal["mean", "variance"] = "mean"
    trials: Annotated[
        int,
        Field(
            ge=10,
            le=2000,
            title="Trials",
            description="シミュレーション試行回数",
        ),
    ] = 100
    sample_size: Annotated[
        int,
        Field(
            ge=5,
            le=500,
            title="Sample Size",
            description="各試行のサンプルサイズ",
        ),
    ] = 30
    confidence_level: float = Field(
        default=0.95,
        description="信頼水準（0.90 / 0.95 / 0.99）",
    )
    true_mean: Annotated[
        float,
        Field(
            ge=-100,
            le=100,
            title="True Mean",
            description="母平均の真の値",
        ),
    ] = 0.0
    true_variance: Annotated[
        float,
        Field(
            ge=0.01,
            le=100,
            title="True Variance",
            description="母分散の真の値",
        ),
    ] = 1.0

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: float) -> float:
        allowed = {0.9, 0.95, 0.99}
        if v not in allowed:
            raise ValueError(
                _("confidence_level must be one of: 0.90, 0.95, or 0.99")
            )
        return v


class CIBound(BaseResult):
    """信頼区間の境界値と包含フラグ"""

    lower: float = Field(description="信頼区間下限")
    upper: float = Field(description="信頼区間上限")
    contains_true: bool = Field(description="真の値を含むか否か")


class ConfidenceIntervalSimResult(BaseResult):
    """信頼区間シミュレーション結果"""

    true_value: float = Field(description="真の値")
    confidence_level: float = Field(description="信頼水準")
    intervals: list[CIBound] = Field(description="各試行の信頼区間リスト")


# ---------------------------------------------------------------------------
# 漸近正規性シミュレーション
# ---------------------------------------------------------------------------


class AsymptoticNormalityRequestBody(BaseRequest):
    """漸近正規性シミュレーションリクエスト"""

    sample_size: Literal[10, 20, 30, 50, 100, 1000] = 100
    num_simulations: Annotated[
        int,
        Field(
            ge=10,
            le=2000,
            title="Num Simulations",
            description="OLS の反復シミュレーション回数",
        ),
    ] = 1000
    true_beta: Annotated[
        float,
        Field(
            ge=-3,
            le=3,
            title="True Beta",
            description="真の傾きパラメータ",
        ),
    ] = 1.0
    error_variance: Annotated[
        float,
        Field(
            ge=0.1,
            le=10,
            title="Error Variance",
            description="誤差の分散",
        ),
    ] = 1.0
    error_type: Literal["normal", "cauchy", "endogenous"] = "normal"
    endogeneity_strength: Annotated[
        float,
        Field(
            ge=0.1,
            le=3.0,
            title="Endogeneity Strength",
            description="内生性の強さ（γ）: endogenous 時のみ有効",
        ),
    ] = 1.0
    x_distribution: XDistributionParams = Field(
        default_factory=XDistributionParams,
        description="説明変数 x の母集団分布パラメータ",
    )


class AsymptoticNormalityResult(BaseResult):
    """漸近正規性シミュレーション結果"""

    beta_estimates: list[float] = Field(description="OLS β̂ の標本リスト")
    true_beta: float = Field(description="真の傾きパラメータ")
    is_asymptotically_normal: bool = Field(
        description="漸近正規性が成立するか否か"
    )
    asymptotic_mean: float | None = Field(
        description="漸近分布の平均（コーシー時は None）"
    )
    asymptotic_variance: float | None = Field(
        description="漸近分布の分散（コーシー時は None）"
    )


# ---------------------------------------------------------------------------
# 一致性シミュレーション
# ---------------------------------------------------------------------------


class ConsistencyRequestBody(BaseRequest):
    """一致性シミュレーションリクエスト"""

    n_max: Annotated[
        int,
        Field(
            ge=50,
            le=5000,
            title="N Max",
            description="サンプルサイズの上限",
        ),
    ] = 500
    true_beta: Annotated[
        float,
        Field(
            ge=-3,
            le=3,
            title="True Beta",
            description="真の傾きパラメータ",
        ),
    ] = 1.0
    error_variance: Annotated[
        float,
        Field(
            ge=0.1,
            le=10,
            title="Error Variance",
            description="誤差の分散",
        ),
    ] = 1.0
    endogenous: bool = Field(
        default=False,
        description="内生性あり (True) / 外生性成立 (False)",
    )
    endogeneity_strength: Annotated[
        float,
        Field(
            ge=0.1,
            le=3.0,
            title="Endogeneity Strength",
            description="内生性の強さ（γ）: endogenous=True 時のみ有効",
        ),
    ] = 1.0
    x_distribution: XDistributionParams = Field(
        default_factory=XDistributionParams,
        description="説明変数 x の母集団分布パラメータ",
    )


class ConsistencyResult(BaseResult):
    """一致性シミュレーション結果"""

    n_values: list[int] = Field(
        description="各推定に使用したサンプルサイズのリスト"
    )
    beta_estimates: list[float] = Field(
        description="各 n における OLS β̂ のリスト"
    )
    true_beta: float = Field(description="真の傾きパラメータ")
    probability_limit: float = Field(
        description="確率極限（外生性: β, 内生性: β + γ/2）"
    )


# ---------------------------------------------------------------------------
# 不偏性シミュレーション
# ---------------------------------------------------------------------------


class UnbiasednessRequestBody(BaseRequest):
    """不偏性シミュレーションリクエスト"""

    num_trials: Annotated[
        int,
        Field(
            ge=10,
            le=2000,
            title="Num Trials",
            description="OLS の反復試行回数",
        ),
    ] = 200
    sample_size: Annotated[
        int,
        Field(
            ge=5,
            le=500,
            title="Sample Size",
            description="各試行のサンプルサイズ",
        ),
    ] = 50
    true_beta: Annotated[
        float,
        Field(
            ge=-3,
            le=3,
            title="True Beta",
            description="真の傾きパラメータ",
        ),
    ] = 1.0
    error_variance: Annotated[
        float,
        Field(
            ge=0.1,
            le=10,
            title="Error Variance",
            description="誤差の分散",
        ),
    ] = 1.0
    x_distribution: XDistributionParams = Field(
        default_factory=XDistributionParams,
        description="説明変数 x の母集団分布パラメータ",
    )


class UnbiasednessResult(BaseResult):
    """不偏性シミュレーション結果"""

    beta_estimates: list[float] = Field(description="各試行の OLS β̂ リスト")
    true_beta: float = Field(description="真の傾きパラメータ")

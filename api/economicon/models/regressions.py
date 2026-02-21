"""回帰分析関連のスキーマ定義"""

from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field, model_validator

from ..i18n.translation import gettext as _
from .common import BaseRequest
from .enums import (
    MissingValueHandlingType,
    RegressionMethodType,
    RegressionType,
    StandardErrorMethodType,
)
from .types import ColumnName, TableName


# 統合リクエストスキーマ
class RegressionRequestBody(BaseRequest):
    """
    統合回帰分析リクエスト

    全ての回帰分析タイプを単一のエンドポイントで扱うための
    統合スキーマです。
    """

    type: RegressionType = Field(alias="type", description="分析タイプ")

    method: RegressionMethodType = Field(
        default=RegressionMethodType.OLS,
        alias="method",
        description="計算手法",
    )

    table_name: TableName

    dependent_variable: Annotated[
        ColumnName,
        Field(description="被説明変数の列名"),
    ]

    explanatory_variables: List[
        Annotated[
            ColumnName,
            Field(description="説明変数の列名"),
        ]
    ]

    standard_error_method: StandardErrorMethodType = Field(
        default=StandardErrorMethodType.NONROBUST,
        alias="standardErrorMethod",
        description="標準誤差計算方法",
    )

    standard_error_params: Dict[str, Any] = Field(
        default_factory=dict,
        alias="standardErrorParams",
        description="標準誤差計算のパラメータ (例: クラスタ変数名)",
    )

    hyper_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        alias="hyperParameters",
        description="ハイパーパラメータ (例: Lasso/Ridge の alpha)",
    )

    use_t_distribution: bool = Field(
        default=True, alias="useTDistribution", description="t分布を使用するか"
    )

    has_const: bool = Field(
        default=True, alias="hasConst", description="定数項を追加するか"
    )

    missing_value_handling: MissingValueHandlingType = Field(
        default=MissingValueHandlingType.REMOVE,
        alias="missingValueHandling",
        description="欠損値の処理方法",
    )

    # パネルデータ分析用
    entity_id_column: Optional[ColumnName] = Field(
        None,
        alias="entityIdColumn",
        description="個体ID列名 (固定効果・変量効果の場合に必要)",
    )

    time_column: Optional[ColumnName] = Field(
        None,
        alias="timeColumn",
        description="時間列名 (パネルデータ分析の場合に使用)",
    )

    # 操作変数法用
    instrumental_variables: Optional[List[ColumnName]] = Field(
        None,
        alias="instrumentalVariables",
        description="操作変数の列名リスト (IV の場合に必要)",
    )

    endogenous_variables: Optional[List[ColumnName]] = Field(
        None,
        alias="endogenousVariables",
        description="内生変数の列名リスト (IV の場合に必要)",
    )

    # Tobit 分析用
    left_censoring_limit: Optional[float] = Field(
        None,
        alias="leftCensoringLimit",
        description="左側打ち切り値 (Tobit の場合に使用、デフォルト0.0)",
    )

    right_censoring_limit: Optional[float] = Field(
        None,
        alias="rightCensoringLimit",
        description="右側打ち切り値 (Tobit の場合に使用)",
    )

    @model_validator(mode="after")
    def validate_analysis_params(self):
        """
        分析パラメータの整合性をバリデーション
        """
        # IV の制限: type=IV または FEIV の場合、instrumental_variables が必要
        if self.type in [RegressionType.IV, RegressionType.FEIV]:
            if not self.instrumental_variables:
                raise ValueError(
                    _(
                        f"type='{self.type}' の場合、instrumentalVariables が必要です"
                    )
                )
        # GMM の制限: type="iv" のみ許可
        if (
            self.method == RegressionMethodType.GMM
            and self.type != RegressionType.IV
        ):
            raise ValueError(
                _(
                    "method='gmm' is the only supported combination with type='iv'"
                )
            )

        # 標準誤差の検証: clustered の場合 groups が必要
        if self.standard_error_method == StandardErrorMethodType.CLUSTERED:
            # パネルデータの場合はentity_id_columnをデフォルトのgroups として使用
            if (
                self.type in [RegressionType.FE, RegressionType.RE]
                and self.entity_id_column
            ):
                # standard_error_paramsにgroupsがない場合、entity_id_columnを設定
                if "groups" not in self.standard_error_params:
                    self.standard_error_params["groups"] = (
                        self.entity_id_column
                    )
            elif "groups" not in self.standard_error_params:
                # パネルデータ以外ではgroupsが必須
                raise ValueError(
                    _(
                        "standardErrorMethod='clustered' の場合、"
                        "standardErrorParams に 'groups' "
                        "(クラスタ変数名) が必要です"
                    )
                )

        # 正則化の検証: lasso, ridge の場合 alpha が必要
        if self.type in [RegressionType.LASSO, RegressionType.RIDGE]:
            if "alpha" not in self.hyper_parameters:
                raise ValueError(
                    _(
                        f"type='{self.type}' の場合、"
                        "hyperParameters に 'alpha' が必要です"
                    )
                )

        # パネルデータ分析の検証
        if self.type in [
            RegressionType.FE,
            RegressionType.RE,
            RegressionType.FEIV,
        ]:
            if not self.entity_id_column:
                raise ValueError(
                    _(f"type='{self.type}' の場合、entityIdColumn が必要です")
                )

        # 操作変数法の検証
        if self.type in [RegressionType.IV, RegressionType.FEIV]:
            if not self.instrumental_variables:
                raise ValueError(
                    _(
                        f"type='{self.type}' の場合、"
                        "instrumentalVariables が必要です"
                    )
                )

        return self

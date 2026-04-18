"""回帰分析関連のスキーマ定義"""

from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, model_validator

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import BaseRequest, BaseResult
from economicon.schemas.entities import RegressionParams, StandardErrorSettings
from economicon.schemas.enums import (
    MissingValueHandlingType,
)
from economicon.schemas.types import (
    ColumnName,
    ResultDescription,
    ResultName,
    TableName,
)


def _coerce_missing_value_handling(v: object) -> MissingValueHandlingType:
    """文字列を MissingValueHandlingType に変換する（strict モード対応）"""
    if isinstance(v, str):
        return MissingValueHandlingType(v)
    return v  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# リクエストボディ
# ---------------------------------------------------------------------------


class RegressionRequestBody(BaseRequest):
    """
    統合回帰分析リクエスト

    全ての回帰分析タイプを単一のエンドポイントで扱うための
    統合スキーマです。
    """

    table_name: Annotated[
        TableName,
        Field(
            description="分析対象のテーブル名。ワークスペース内に存在するテーブル名を指定してください。"
        ),
    ]
    result_name: ResultName
    description: ResultDescription
    dependent_variable: Annotated[
        ColumnName,
        Field(
            title="Dependent Variable",
            description="被説明変数（目的変数）の列名。テーブル内に存在するカラム名を指定してください。",
        ),
    ]
    explanatory_variables: Annotated[
        list[ColumnName],
        Field(
            title="Explanatory Variables",
            description="説明変数の列名のリスト。テーブル内に存在するカラム名を指定してください。",
        ),
    ]
    has_const: Annotated[
        bool,
        Field(
            default=True,
            alias="hasConst",
            title="Has Const",
            description="定数項を設計行列に追加するかどうか",
        ),
    ]
    missing_value_handling: Annotated[
        MissingValueHandlingType,
        BeforeValidator(_coerce_missing_value_handling),
        Field(
            default=MissingValueHandlingType.REMOVE,
            alias="missingValueHandling",
            title="Missing Value Handling",
            description="欠損値の処理方法"
            "（remove: 該当行を削除、ignore: そのまま使用、"
            "error: エラーとして扱う）",
        ),
    ]

    # 統計手法ごとの可変部分
    analysis: Annotated[
        RegressionParams,
        Field(
            title="Regression Analysis Params",
            description="回帰分析手法の詳細パラメータ。"
            "method フィールドで手法（ols, fe, re, iv 等）を指定します。",
        ),
    ]

    # 標準誤差の設定
    standard_error: Annotated[
        StandardErrorSettings,
        Field(
            title="Standard Error Settings",
            description="標準誤差の計算方法設定。"
            "nonrobust, robust（HC）, cluster, "
            "hac（Newey-West）から選択します。",
        ),
    ]

    @model_validator(mode="after")
    def _validate_dependent_not_in_explanatory(
        self,
    ) -> RegressionRequestBody:
        """dependent が explanatory に含まれないことを検証。"""
        if self.dependent_variable in set(self.explanatory_variables):
            raise ValueError(
                _(
                    "dependentVariable '{}' must not appear"
                    " in explanatoryVariables."
                ).format(self.dependent_variable)
            )
        return self


# ---------------------------------------------------------------------------
# 回帰分析実行
# ---------------------------------------------------------------------------


class RegressionResult(BaseResult):
    """回帰分析実行レスポンス"""

    result_id: str = Field(
        title="Result ID",
        description="保存された分析結果の一意 ID",
    )


# ---------------------------------------------------------------------------
# 診断列追加（予測値・残差）
# ---------------------------------------------------------------------------


class AddDiagnosticColumnsRequestBody(BaseRequest):
    """
    推定済みモデルから予測値・残差を抽出してテーブルに列追加するリクエスト
    """

    table_name: Annotated[
        TableName,
        Field(
            description="追加先テーブル名。ワークスペース内に存在するテーブル名を"
            "指定してください。",
        ),
    ]
    result_id: Annotated[
        str,
        Field(
            alias="resultId",
            description="対象の分析結果 ID（AnalysisResult の UUID）",
        ),
    ]
    target: Annotated[
        Literal["fitted", "residual", "both"],
        Field(
            description="追加する値の種類。"
            "fitted: 予測値のみ、residual: 残差のみ、both: 両方",
        ),
    ]
    standardized: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "True の場合、標準化残差"
                "（studentized internal）を追加する。"
                "OLS/Logit/Probit のみ有効。"
            ),
        ),
    ] = False
    include_interval: Annotated[
        bool,
        Field(
            default=False,
            alias="includeInterval",
            description="True の場合、予測値の 95%信頼区間列を追加する。"
            "OLS/FE/RE/IV で有効。",
        ),
    ] = False
    fe_type: Annotated[
        Literal["total", "within"],
        Field(
            default="total",
            alias="feType",
            description="FE/RE モデルの予測値タイプ。"
            "total: 固定効果を含む予測（effects=True）、"
            "within: 固定効果を除いた変動成分（effects=False）。"
            "FE/RE 以外では無視される。",
        ),
    ] = "total"
    # Eco-Note A: Logit/Probit の残差種別オプション
    binary_residual_type: Annotated[
        Literal["raw", "deviance"],
        Field(
            default="raw",
            alias="binaryResidualType",
            description="Logit/Probit の残差種別。"
            "raw: 生残差 (y - p̂)、"
            "deviance: デビアンス残差"
            " sign(y-p̂)√(-2[y·log(p̂)+(1-y)·log(1-p̂)])。"
            "OLS などその他のモデルでは無視される。",
        ),
    ] = "raw"
    # Eco-Note B: Tobit の予測値種別オプション
    tobit_fitted_type: Annotated[
        Literal["latent", "observable"],
        Field(
            default="latent",
            alias="tobitFittedType",
            description="Tobit モデルの予測値種別。"
            "latent: 潜在変数の予測値 x'β（デフォルト）、"
            "observable: 観測値の無条件期待値 E[y|x]"
            "（打ち切りを考慮した期待値）。"
            "Tobit 以外のモデルでは無視される。",
        ),
    ] = "latent"


class AddDiagnosticColumnsResult(BaseResult):
    """診断列追加レスポンス"""

    table_name: str = Field(
        alias="tableName",
        title="Table Name",
        description="更新されたテーブル名",
    )
    added_columns: list[str] = Field(
        alias="addedColumns",
        title="Added Columns",
        description="追加された列名のリスト",
    )

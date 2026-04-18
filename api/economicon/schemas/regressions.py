"""回帰分析関連のスキーマ定義"""

from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, model_validator

from economicon.schemas.common import (
    BaseRequest,
    BaseResult,
    check_column_overlap,
)
from economicon.schemas.entities import (
    FEParams,
    FGLSParams,
    GLSParams,
    InstrumentalVariablesParams,
    PanelIvParams,
    RegressionParams,
    REParams,
    StandardErrorSettings,
    WLSParams,
)
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


def _collect_reserved(
    analysis: RegressionParams,
    rs: dict[str, str],
    rv: dict[str, list[str]],
) -> None:
    """分析手法に応じた予約列を rs / rv に収集する。"""
    if isinstance(analysis, (FEParams, REParams, PanelIvParams)):
        rs["entityIdColumn"] = analysis.entity_id_column
        if analysis.time_column:
            rs["timeColumn"] = analysis.time_column
    if isinstance(analysis, (InstrumentalVariablesParams, PanelIvParams)):
        rv["instrumentalVariables"] = analysis.instrumental_variables
        rv["endogenousVariables"] = analysis.endogenous_variables
    if isinstance(analysis, WLSParams):
        rs["weightsColumn"] = analysis.weights_column
    if isinstance(analysis, FGLSParams | GLSParams):
        pass  # sigma_table_name はテーブル名のため列重複チェック不要


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
    def _validate_column_overlap(
        self,
    ) -> RegressionRequestBody:
        """手法別の列重複チェック。

        _collect_reserved で予約列セットを構築し、
        check_column_overlap に委譲する。

        チェック内容:
        - explanatoryVariables 内の重複
        - dependentVariable / explanatoryVariables が
          各予約列グループと重複しないこと
        - FE/RE: entityIdColumn / timeColumn との重複禁止
        - IV: instrumentalVariables / endogenousVariables
          との重複禁止
        - PanelIV: 上記すべて
        """
        rs: dict[str, str] = {}
        rv: dict[str, list[str]] = {}
        _collect_reserved(self.analysis, rs, rv)
        check_column_overlap(
            dependent_variable=self.dependent_variable,
            explanatory_variables=self.explanatory_variables,
            reserved_scalars=rs or None,
            reserved_vectors=rv or None,
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


# ---------------------------------------------------------------------------
# 分析結果データ構造（result_store に格納される詳細データ）
# ---------------------------------------------------------------------------


class RegressionParameter(BaseResult):
    """回帰係数の推定結果（1変数分）。

    statsmodels / linearmodels 共通フォーマット。
    NaN が返るフィールドは None として格納する。
    """

    variable: str = Field(description="変数名")
    coefficient: float = Field(description="係数推定値")
    standard_error: float | None = Field(default=None, description="標準誤差")
    t_value: float | None = Field(default=None, description="t 統計量")
    p_value: float | None = Field(default=None, description="p 値")
    confidence_interval_lower: float | None = Field(
        default=None, description="信頼区間下限"
    )
    confidence_interval_upper: float | None = Field(
        default=None, description="信頼区間上限"
    )


class RegressionModelStatistics(BaseResult):
    """モデル統計量（手法により一部 null）。

    フィールド命名規則:
    - alias_generator=to_camel が適用されるが、
      formatter が非標準の大文字を使うフィールドは
      Field(alias=...) で明示的に上書きする。
    """

    n_observations: int = Field(description="観測数")
    # --- OLS / IV ---
    r2: float | None = Field(
        default=None,
        alias="R2",
        description="決定係数 R²（OLS / IV など）",
    )
    adjusted_r2: float | None = Field(
        default=None,
        description="自由度修正済み R²（OLS）",
    )
    f_value: float | None = Field(
        default=None,
        description="F 統計量（OLS / FE / RE）",
    )
    f_probability: float | None = Field(
        default=None,
        description="F 検定 p 値",
    )
    # --- OLS / Logit / Probit / Tobit ---
    aic: float | None = Field(
        default=None,
        alias="AIC",
        description="AIC（赤池情報量基準）",
    )
    bic: float | None = Field(
        default=None,
        alias="BIC",
        description="BIC（ベイズ情報量基準）",
    )
    log_likelihood: float | None = Field(
        default=None,
        description="対数尤度",
    )
    # --- Logit / Probit ---
    pseudo_r_squared: float | None = Field(
        default=None,
        description="疑似 R²（Logit / Probit）",
    )
    # --- FE / RE ---
    n_entities: int | None = Field(
        default=None,
        description="個体数（FE / RE）",
    )
    r2_within: float | None = Field(
        default=None,
        alias="R2Within",
        description="within R²（FE / RE）",
    )
    r2_between: float | None = Field(
        default=None,
        alias="R2Between",
        description="between R²（FE / RE）",
    )
    r2_overall: float | None = Field(
        default=None,
        alias="R2Overall",
        description="overall R²（FE / RE）",
    )


class IVTestResult(BaseResult):
    """IV 推定の個別診断テスト結果。"""

    statistic: float = Field(description="検定統計量")
    p_value: float = Field(description="p 値")
    description: str = Field(description="検定の説明")


class FirstStageResult(BaseResult):
    """第一段階回帰の検定統計量（弱い操作変数の検定）。"""

    f_statistic: float = Field(
        alias="fStatistic",
        description="F 統計量",
    )
    p_value: float = Field(description="p 値")
    description: str = Field(description="検定の説明")


class RegressionDiagnostics(BaseResult):
    """診断統計（Optional フラット設計）。

    手法によって非 null なフィールドが異なる。
    現時点では IV 推定の診断統計のみを保持する。
    将来の拡張（PanelIV / 構造推定など）はフィールド追加で対応する。
    """

    wu_hausman_test: IVTestResult | None = Field(
        default=None,
        description=("Durbin-Wu-Hausman 内生性検定。IV 推定時のみ非 null。"),
    )
    sargan_test: IVTestResult | None = Field(
        default=None,
        description=(
            "Sargan 過剰識別制約検定。"
            "操作変数が内生変数より多い場合のみ非 null。"
        ),
    )
    first_stage: dict[str, FirstStageResult] | None = Field(
        default=None,
        description=(
            "内生変数ごとの第一段階 F 統計量。"
            "キー: 内生変数名、値: FirstStageResult。"
        ),
    )


class RegressionResultData(BaseResult):
    """
    回帰分析結果の詳細データ

    analysis_result_store に result_data として格納される。
    GET /analysis/results/{id} で取得可能。
    手法によって非 null なフィールドが異なる。
    """

    table_name: str = Field(description="分析対象テーブル名")
    dependent_variable: str = Field(description="被説明変数名")
    explanatory_variables: list[str] = Field(description="説明変数名リスト")
    endogenous_variables: list[str] | None = Field(
        default=None,
        description="内生変数名リスト（IV / PanelIV のみ非 null）",
    )
    instrumental_variables: list[str] | None = Field(
        default=None,
        description="操作変数名リスト（IV / PanelIV のみ非 null）",
    )
    regression_result: str = Field(
        description=(
            "推定結果サマリーテキスト（statsmodels / linearmodels 出力）"
        )
    )
    parameters: list[RegressionParameter] = Field(
        description="回帰係数の推定結果リスト"
    )
    model_statistics: RegressionModelStatistics = Field(
        description="モデル統計量"
    )
    diagnostics: RegressionDiagnostics | None = Field(
        default=None,
        description=(
            "診断統計。OLS / FE / RE では null。"
            "IV では Durbin-Wu-Hausman / Sargan /"
            " 第一段階 F 統計量を格納。"
        ),
    )

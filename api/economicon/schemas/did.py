"""差の差（DID）分析関連のスキーマ定義"""

from typing import Annotated

from pydantic import BeforeValidator, Field, model_validator

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import BaseRequest, BaseResult
from economicon.schemas.entities import StandardErrorSettings
from economicon.schemas.enums import MissingValueHandlingType
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


class DIDRequestBody(BaseRequest):
    """
    差の差（DID）分析リクエスト

    Two-Way Fixed Effects（TWFE）による差の差推定と、
    オプションで Event Study を実行します。
    交差項（treated × post）はサービス層で自動生成します。
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
    dependent_variable: Annotated[
        ColumnName,
        Field(
            description=(
                "被説明変数（目的変数）の列名。"
                "テーブル内に存在する数値型カラムを指定してください。"
            ),
        ),
    ]
    explanatory_variables: Annotated[
        list[ColumnName],
        Field(
            default_factory=list,
            description=(
                "追加の共変量（コントロール変数）の列名リスト。"
                "treatment_column / post_column との重複は不可。"
            ),
        ),
    ]
    treatment_column: Annotated[
        ColumnName,
        Field(
            description=(
                "処置群ダミー列名（treated_i）。"
                "個体レベルの 0/1 変数。処置群=1、対照群=0。"
            ),
        ),
    ]
    post_column: Annotated[
        ColumnName,
        Field(
            description=(
                "処置後ダミー列名（post_t）。"
                "時点レベルの 0/1 変数。処置後=1、処置前=0。"
            ),
        ),
    ]
    time_column: Annotated[
        ColumnName,
        Field(
            description=(
                "時点列名。数値型または Date 型。"
                "Event Study 実行時は整数型を推奨します。"
            ),
        ),
    ]
    entity_id_column: Annotated[
        ColumnName,
        Field(
            description=("個体 ID 列名。TWFE の個体固定効果に使用します。"),
        ),
    ]
    include_event_study: Annotated[
        bool,
        Field(
            default=False,
            alias="includeEventStudy",
            description=(
                "Event Study を実行するかどうか。"
                "True の場合、各時点の処置効果係数（δ_k）を推定します。"
            ),
        ),
    ]
    base_period: Annotated[
        int | None,
        Field(
            default=None,
            alias="basePeriod",
            description=(
                "Event Study の基準期（処置効果をゼロに固定する時点）。"
                "null の場合は処置直前期（通常 -1）を自動選択します。"
                "include_event_study=true のときのみ有効です。"
            ),
        ),
    ]
    max_pre_periods: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            alias="maxPrePeriods",
            description=(
                "Event Study で表示する処置前の最大期間数。"
                "null の場合はデータ内の全処置前期間を使用します。"
            ),
        ),
    ]
    max_post_periods: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            alias="maxPostPeriods",
            description=(
                "Event Study で表示する処置後の最大期間数。"
                "null の場合はデータ内の全処置後期間を使用します。"
            ),
        ),
    ]
    missing_value_handling: Annotated[
        MissingValueHandlingType,
        BeforeValidator(_coerce_missing_value_handling),
        Field(
            default=MissingValueHandlingType.REMOVE,
            alias="missingValueHandling",
            description=(
                "欠損値の処理方法。"
                "remove: 該当行を削除、ignore: そのまま使用、"
                "error: エラーとして扱う。"
            ),
        ),
    ]
    standard_error: Annotated[
        StandardErrorSettings,
        Field(
            description=(
                "標準誤差の計算方法。"
                "DID では個体レベルのクラスタ標準誤差（cluster）を推奨します。"
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
            description="信頼区間の水準（デフォルト: 0.95）",
        ),
    ]

    @model_validator(mode="after")
    def _validate_event_study_params(
        self,
    ) -> DIDRequestBody:
        """includeEventStudy=False のとき ES パラメータを禁止する。"""
        if not self.include_event_study:
            if self.base_period is not None:
                raise ValueError(
                    _(
                        "basePeriod can only be set"
                        " when includeEventStudy is true."
                    )
                )
            if self.max_pre_periods is not None:
                raise ValueError(
                    _(
                        "maxPrePeriods can only be set"
                        " when includeEventStudy is true."
                    )
                )
            if self.max_post_periods is not None:
                raise ValueError(
                    _(
                        "maxPostPeriods can only be set"
                        " when includeEventStudy is true."
                    )
                )
        return self

    @model_validator(mode="after")
    def _validate_column_overlap(
        self,
    ) -> DIDRequestBody:
        """リクエスト内のパラメータ間列重複を検証する。

        チェック内容:
        - explanatoryVariables に重複列名がないこと
        - treatmentColumn/postColumn/entityIdColumn/timeColumn が
          互いに重複しないこと
        - dependentVariable が予約列と重複しないこと
        - dependentVariable が explanatoryVariables に含まれないこと
        - explanatoryVariables が予約列と重複しないこと
        """
        expl = set(self.explanatory_variables)

        # W2: explanatory に重複列名がないこと
        if len(self.explanatory_variables) != len(expl):
            raise ValueError(
                _(
                    "explanatoryVariables must not contain"
                    " duplicate column names."
                )
            )

        # W1: 予約列が互いに重複しないこと
        reserved_list = [
            self.treatment_column,
            self.post_column,
            self.entity_id_column,
            self.time_column,
        ]
        if len(reserved_list) != len(set(reserved_list)):
            raise ValueError(
                _(
                    "treatmentColumn / postColumn / entityIdColumn"
                    " / timeColumn must all be distinct."
                )
            )

        reserved = set(reserved_list)

        # C1: dependent が予約列と重複しないこと
        if self.dependent_variable in reserved:
            raise ValueError(
                _(
                    "dependentVariable '{}' must not overlap with"
                    " treatmentColumn / postColumn"
                    " / entityIdColumn / timeColumn."
                ).format(self.dependent_variable)
            )

        # dependent が explanatory に含まれないこと
        if self.dependent_variable in expl:
            raise ValueError(
                _(
                    "dependentVariable '{}' must not appear"
                    " in explanatoryVariables."
                ).format(self.dependent_variable)
            )

        # explanatory が予約列と重複しないこと
        overlap = reserved & expl
        if overlap:
            raise ValueError(
                _(
                    "explanatoryVariables must not overlap with"
                    " treatmentColumn / postColumn / entityIdColumn"
                    " / timeColumn: {}"
                ).format(", ".join(sorted(overlap)))
            )
        return self


# ---------------------------------------------------------------------------
# DID 分析実行レスポンス
# ---------------------------------------------------------------------------


class DIDResult(BaseResult):
    """DID 分析実行レスポンス"""

    result_id: str = Field(
        title="Result ID",
        description="保存された分析結果の一意 ID",
    )


# ---------------------------------------------------------------------------
# 分析結果データ構造（result_store に格納される詳細データ）
# ---------------------------------------------------------------------------


class DIDEstimate(BaseResult):
    """
    DID 推定量（ATT: Average Treatment Effect on the Treated）

    交差項 (treated × post) の係数。TWFE 推定に基づく。
    """

    coefficient: float = Field(description="DID 推定係数（ATT）")
    standard_error: float = Field(description="標準誤差")
    t_value: float = Field(description="t 統計量")
    p_value: float = Field(description="p 値")
    ci_lower: float = Field(description="信頼区間下限")
    ci_upper: float = Field(description="信頼区間上限")
    description: str = Field(
        description=(
            "推定量の説明文。例: "
            "'ATT: Average Treatment Effect on the Treated (TWFE)'"
        )
    )


class DIDParameter(BaseResult):
    """回帰係数（共変量・定数項など交差項以外の係数）"""

    name: str = Field(description="変数名")
    coefficient: float = Field(description="係数推定値")
    standard_error: float = Field(description="標準誤差")
    t_value: float = Field(description="t 統計量")
    p_value: float = Field(description="p 値")
    ci_lower: float = Field(description="信頼区間下限")
    ci_upper: float = Field(description="信頼区間上限")


class DIDModelStatistics(BaseResult):
    """モデル統計量"""

    n_observations: int = Field(description="総観測数")
    n_treated: int = Field(description="処置群のユニーク個体数")
    n_control: int = Field(description="対照群のユニーク個体数")
    n_periods: int = Field(description="時点数（ユニーク）")
    r2: float = Field(description="決定係数 R²")
    adjusted_r2: float = Field(description="自由度修正済み R²")
    f_value: float = Field(description="F 統計量")
    f_probability: float = Field(description="F 検定の p 値")


class PreTrendTest(BaseResult):
    """
    並行トレンド仮定の検定（Wald/F 検定）

    Event Study の処置前期間係数が同時にゼロであることを検定する。
    帰無仮説 H0: δ_k = 0 (k < 0, k ≠ base_period)
    非有意（p > 0.05）が並行トレンド仮定を支持する。
    """

    f_statistic: float = Field(
        description="F 統計量（処置前係数の Wald 検定）"
    )
    df1: int = Field(description="分子の自由度（処置前期間数 - 1）")
    df2: int = Field(description="分母の自由度")
    p_value: float = Field(description="p 値")
    description: str = Field(
        description=(
            "検定結果の解釈文。例: "
            "'Test for parallel trends assumption. "
            "Non-significant p-value supports parallel trends.'"
        )
    )


class DIDDiagnostics(BaseResult):
    """診断統計量"""

    # Eco-Note: pre_trend_test は Event Study を実行した場合のみ非 null。
    # include_event_study=False 時は null となる。
    pre_trend_test: PreTrendTest | None = Field(
        default=None,
        description=(
            "並行トレンド仮定の Wald 検定結果。"
            "include_event_study=true のときのみ非 null。"
        ),
    )


class EventStudyPoint(BaseResult):
    """
    Event Study の各時点推定値

    period は処置時点 t=0 からの相対期間。
    base_period の係数は 0（固定）。
    """

    period: int = Field(
        description="処置からの相対期間（例: -2, -1, 0, 1, 2）"
    )
    coefficient: float = Field(description="係数推定値 δ_k")
    standard_error: float = Field(description="標準誤差")
    t_value: float = Field(description="t 統計量")
    p_value: float = Field(description="p 値")
    ci_lower: float = Field(description="信頼区間下限")
    ci_upper: float = Field(description="信頼区間上限")


class DIDResultData(BaseResult):
    """
    DID 分析結果の詳細データ

    analysis_result_store に result_data として格納される。
    GET /analysis/results/{id} で取得可能。
    """

    table_name: str = Field(description="分析対象テーブル名")
    dependent_variable: str = Field(description="被説明変数名")
    treatment_column: str = Field(description="処置群ダミー列名")
    post_column: str = Field(description="処置後ダミー列名")
    time_column: str = Field(description="時点列名")
    entity_id_column: str = Field(description="個体 ID 列名")
    confidence_level: float = Field(description="信頼区間の水準")
    did_estimate: DIDEstimate = Field(description="DID 推定量（ATT）")
    parameters: list[DIDParameter] = Field(
        description="共変量・定数項の係数リスト（交差項を除く）"
    )
    model_statistics: DIDModelStatistics = Field(description="モデル統計量")
    diagnostics: DIDDiagnostics = Field(description="診断統計量")
    event_study: list[EventStudyPoint] | None = Field(
        default=None,
        description=(
            "Event Study の各時点係数リスト。"
            "include_event_study=false の場合は null。"
        ),
    )

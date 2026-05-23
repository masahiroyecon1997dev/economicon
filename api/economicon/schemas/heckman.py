"""ヘックマン2段階推定関連のスキーマ定義"""

from typing import Annotated, Self

from pydantic import BeforeValidator, Field, model_validator

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import BaseRequest, BaseResult
from economicon.schemas.enums import MissingValueHandlingType
from economicon.schemas.types import (
    ColumnName,
    ResultDescription,
    ResultName,
    TableName,
)


def _coerce_missing_value_handling(
    v: object,
) -> MissingValueHandlingType:
    """文字列を MissingValueHandlingType に変換する。"""
    if isinstance(v, str):
        return MissingValueHandlingType(v)
    return v  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# リクエストボディ
# ---------------------------------------------------------------------------


class HeckmanRequestBody(BaseRequest):
    """
    ヘックマン2段階推定リクエスト

    選択方程式（Probit）と結果方程式（OLS）の2段階推定
    によりサンプルセレクションバイアスを補正します。
    """

    table_name: Annotated[
        TableName,
        Field(
            description=(
                "分析対象のテーブル名。"
                "ワークスペース内に存在するテーブル名を"
                "指定してください。"
            ),
        ),
    ]
    result_name: ResultName
    description: ResultDescription
    dependent_variable: Annotated[
        ColumnName,
        Field(
            description=(
                "結果方程式の被説明変数列名。"
                "選択サンプル（selectionColumn=1）のみで"
                "推定されます。"
            ),
        ),
    ]
    explanatory_variables: Annotated[
        list[ColumnName],
        Field(description="結果方程式の説明変数列名リスト。"),
    ]
    selection_column: Annotated[
        ColumnName,
        Field(
            description=(
                "選択ダミー列名（0/1）。1 = 結果変数が観測されるサンプル。"
            ),
        ),
    ]
    selection_variables: Annotated[
        list[ColumnName],
        Field(
            description=(
                "選択方程式（Probit）の説明変数列名リスト。"
                "除外制約として explanatoryVariables にない"
                "変数を 1 つ以上含む必要があります。"
            ),
        ),
    ]
    has_const: Annotated[
        bool,
        Field(
            default=True,
            description=("結果方程式（Step 2 OLS）に定数項を追加するか。"),
        ),
    ]
    missing_value_handling: Annotated[
        MissingValueHandlingType,
        BeforeValidator(_coerce_missing_value_handling),
        Field(
            default=MissingValueHandlingType.REMOVE,
            alias="missingValueHandling",
            description=(
                "欠損値の処理方法（remove: 削除, ignore: 無視, error: エラー）"
            ),
        ),
    ]
    report_first_stage: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "1 段階目（Probit）の推定結果を"
                "レスポンスの firstStage に含めるか。"
            ),
        ),
    ]

    @model_validator(mode="after")
    def _check_exclusion_restriction(
        self,
    ) -> Self:
        """除外制約の検証。

        selectionVariables が explanatoryVariables にない
        変数を 1 つ以上含むことを確認する。

        Eco-Note: 除外制約は Heckman 推定の識別条件。
        選択方程式のみに現れる外生変数（除外変数）が
        存在しないと λ（逆ミルズ比）と説明変数が
        多重共線性を生じ係数が不安定になる。
        """
        extra = set(self.selection_variables) - set(self.explanatory_variables)
        if not extra:
            raise ValueError(
                _(
                    "selectionVariables must include at least"
                    " one variable not in explanatoryVariables"
                    " (exclusion restriction)."
                )
            )
        return self


# ---------------------------------------------------------------------------
# レスポンス
# ---------------------------------------------------------------------------


class HeckmanResult(BaseResult):
    """ヘックマン2段階推定実行レスポンス"""

    result_id: str = Field(
        title="Result ID",
        description="保存された分析結果の一意 ID",
    )

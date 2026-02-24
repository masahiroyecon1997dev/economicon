"""回帰分析関連のスキーマ定義"""

from typing import Annotated, Any

from pydantic import BeforeValidator, Field

from economicon.models.common import BaseRequest, BaseResult
from economicon.models.entities import RegressionParams, StandardErrorSettings
from economicon.models.enums import (
    MissingValueHandlingType,
)
from economicon.models.types import ColumnName, TableName


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
    result_name: Annotated[
        str,
        Field(
            default="",
            title="Result Name",
            max_length=128,
            description="分析結果の名前（省略時は被説明変数名を使用）",
        ),
    ]
    description: Annotated[
        str,
        Field(
            default="",
            title="Description",
            max_length=512,
            description="分析結果の説明メモ",
        ),
    ]
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


# ---------------------------------------------------------------------------
# レスポンス（Result）
# ---------------------------------------------------------------------------


class RegressionResult(BaseResult):
    """回帰分析実行レスポンス"""

    result_id: str = Field(
        title="Result ID",
        description="保存された分析結果の一意 ID",
    )


class GetAllAnalysisResultsResult(BaseResult):
    """全分析結果サマリー取得レスポンス"""

    results: list[Any] = Field(
        title="Results",
        description="分析結果のサマリーリスト",
    )


class GetAnalysisResultResult(BaseResult):
    """分析結果詳細取得レスポンス"""

    result: Any = Field(
        title="Result",
        description="分析結果の詳細データ",
    )


class DeleteAnalysisResultResult(BaseResult):
    """分析結果削除レスポンス"""

    deleted_result_id: str = Field(
        title="Deleted Result ID",
        description="削除した分析結果の ID",
    )


class ClearAllAnalysisResultsResult(BaseResult):
    """全分析結果クリアレスポンス"""

    message: str = Field(
        title="Message",
        description="処理結果メッセージ",
    )

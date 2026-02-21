"""回帰分析関連のスキーマ定義"""

from typing import Annotated, List

from pydantic import Field

from .common import BaseRequest
from .entities import RegressionParams, StandardErrorSettings
from .enums import (
    MissingValueHandlingType,
)
from .types import ColumnName, TableName


class RegressionRequestBody(BaseRequest):
    """
    統合回帰分析リクエスト

    全ての回帰分析タイプを単一のエンドポイントで扱うための
    統合スキーマです。
    """

    table_name: TableName
    result_name: str = Field(
        default="",
        max_length=128,
        description="分析結果の名前（省略時は被説明変数名を使用）",
    )
    description: str = Field(
        default="",
        max_length=512,
        description="分析結果の説明",
    )
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
    has_const: bool = Field(
        default=True, alias="hasConst", description="定数項を追加するか"
    )
    missing_value_handling: MissingValueHandlingType = Field(
        default=MissingValueHandlingType.REMOVE,
        alias="missingValueHandling",
        description="欠損値の処理方法",
    )

    # 統計手法ごとの可変部分
    analysis: RegressionParams

    # 標準誤差の設定
    standard_error: StandardErrorSettings

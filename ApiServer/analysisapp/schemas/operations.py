"""その他の操作関連のスキーマ定義"""
from pydantic import Field
from typing import Any
from .common import TableRequest


class InputCellDataRequest(TableRequest):
    """セルデータ入力リクエスト"""
    columnName: str = Field(..., description="カラム名")
    rowIndex: int = Field(..., description="行インデックス")
    newValue: Any = Field(..., description="新しい入力値")


class FilterSingleConditionRequest(TableRequest):
    """単一条件フィルタリクエスト"""
    newTableName: str = Field(..., description="新しいテーブル名")
    columnName: str = Field(..., description="対象カラム名")
    condition: str = Field(..., description="条件")
    isCompareColumn: str = Field(..., description="比較対象がカラムかどうか")
    compareValue: Any = Field(..., description="比較値")

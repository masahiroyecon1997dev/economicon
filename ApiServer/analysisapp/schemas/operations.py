"""その他の操作関連のスキーマ定義"""
from pydantic import Field
from typing import Any
from .common import TableRequest


class InputCellDataRequest(TableRequest):
    """セルデータ入力リクエスト"""
    rowNumber: int = Field(..., description="行番号")
    columnName: str = Field(..., description="カラム名")
    rowIndex: int = Field(..., description="行インデックス")
    newValue: Any = Field(..., description="新しい入力値")

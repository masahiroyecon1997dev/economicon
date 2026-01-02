"""カラム操作関連のスキーマ定義"""
from pydantic import BaseModel, Field
from typing import Optional, List
from .common import TableRequest, ColumnRequest


class AddColumnRequest(TableRequest):
    """カラム追加リクエスト"""
    newColumnName: str = Field(..., description="新しいカラム名")
    addPositionColumn: str = Field(..., description="追加位置の基準となるカラム名")


class DeleteColumnRequest(ColumnRequest):
    """カラム削除リクエスト"""
    pass


class RenameColumnRequest(ColumnRequest):
    """カラム名変更リクエスト"""
    newColumnName: str = Field(..., description="新しいカラム名")


class DuplicateColumnRequest(ColumnRequest):
    """カラム複製リクエスト"""
    newColumnName: str = Field(..., description="新しいカラム名")
    addPositionColumn: str = Field(..., description="追加位置の基準となるカラム名")


class CalculateColumnRequest(TableRequest):
    """カラム計算リクエスト"""
    formula: str = Field(..., description="計算式")
    newColumnName: str = Field(..., description="結果を格納するカラム名")


class TransformColumnRequest(ColumnRequest):
    """カラム変換リクエスト"""
    transformType: str = Field(..., description="変換タイプ")
    parameters: dict = Field(default_factory=dict, description="変換パラメータ")


class SortColumnsRequest(TableRequest):
    """カラムソートリクエスト"""
    columnOrder: List[str] = Field(..., description="カラムの並び順")


class GetColumnListRequest(TableRequest):
    """カラムリスト取得リクエスト"""
    pass

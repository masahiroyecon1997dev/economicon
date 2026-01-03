"""テーブル操作関連のスキーマ定義"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from .common import TableRequest


class CreateTableRequest(TableRequest):
    """テーブル作成リクエスト"""
    tableNumberOfRows: int = Field(..., description="テーブルの行数")
    columnNames: List[str] = Field(..., description="カラム名のリスト")


class RenameTableRequest(BaseModel):
    """テーブル名変更リクエスト"""
    oldTableName: str = Field(..., description="元のテーブル名")
    newTableName: str = Field(..., description="新しいテーブル名")


class CreateSimulationDataTableRequest(TableRequest):
    """シミュレーションデータテーブル作成リクエスト"""
    tableNumberOfRows: int = Field(..., description="テーブルの行数")
    columnSettings: List[Dict[str, Any]] = Field(..., description="カラム設定のリスト")


class CreateJoinTableRequest(BaseModel):
    """結合テーブル作成リクエスト"""
    joinTableName: str = Field(..., description="結合後のテーブル名")
    leftTableName: str = Field(..., description="左側のテーブル名")
    rightTableName: str = Field(..., description="右側のテーブル名")
    leftKeyColumnNames: List[str] = Field(..., description="左側の結合キーカラム名のリスト")
    rightKeyColumnNames: List[str] = Field(..., description="右側の結合キーカラム名のリスト")
    joinType: str = Field(..., description="結合タイプ (inner, left, right, outer)")


class CreateUnionTableRequest(BaseModel):
    """ユニオンテーブル作成リクエスト"""
    unionTableName: str = Field(..., description="ユニオン後のテーブル名")
    tableNames: List[str] = Field(..., description="結合するテーブル名のリスト")
    columnNames: List[str] = Field(default_factory=list, description="対象カラム名のリスト")


class ClearTablesRequest(BaseModel):
    """テーブルクリアリクエスト（パラメータなし）"""
    pass

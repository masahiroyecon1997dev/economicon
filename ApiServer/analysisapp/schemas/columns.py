"""カラム操作関連のスキーマ定義"""
from typing import Dict, List, Optional

from pydantic import Field

from .common import BaseModel


class AddColumnRequest(BaseModel):
    """カラム追加リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    newColumnName: str = Field(..., description="新しいカラム名")
    addPositionColumn: str = Field(..., description="追加位置の基準となるカラム名")


class DeleteColumnRequest(BaseModel):
    """カラム削除リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    columnName: str = Field(..., description="カラム名")


class RenameColumnRequest(BaseModel):
    """カラム名変更リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    oldColumnName: str = Field(..., description="元のカラム名")
    newColumnName: str = Field(..., description="新しいカラム名")


class DuplicateColumnRequest(BaseModel):
    """カラム複製リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    sourceColumnName: str = Field(..., description="元のカラム名")
    newColumnName: str = Field(..., description="新しいカラム名")


class CalculateColumnRequest(BaseModel):
    """カラム計算リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    newColumnName: str = Field(..., description="新しいカラム名")
    calculationExpression: str = Field(..., description="計算式")


class AddDummyColumnRequest(BaseModel):
    """ダミー変数カラム追加リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    sourceColumnName: str = Field(..., description="元となるカラム名")
    dummyColumnName: str = Field(..., description="ダミー変数カラム名")
    targetValue: str = Field(..., description="1にする対象の値")


class AddLagLeadColumnRequest(BaseModel):
    """ラグ・リードカラム追加リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    sourceColumn: str = Field(..., description="元となるカラム名")
    newColumnName: str = Field(..., description="新しいカラム名")
    periods: int = Field(..., description="ラグ・リード期間")
    groupColumns: List[str] = Field(
        default_factory=list,
        description="グループ化するカラムのリスト"
    )


class AddSimulationColumnRequest(BaseModel):
    """シミュレーションカラム追加リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    newColumnName: str = Field(..., description="新しいカラム名")
    distributionType: str = Field(..., description="分布の種類")
    distributionParams: dict = Field(..., description="分布のパラメータ")


class SortColumnsRequest(BaseModel):
    """カラムソートリクエスト"""
    tableName: str = Field(..., description="テーブル名")
    sortColumns: List[Dict[str, str]] = Field(
        ...,
        description="ソート設定のリスト"
    )


class TransformColumnRequest(BaseModel):
    """カラム変換リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    sourceColumnName: str = Field(..., description="元となるカラム名")
    newColumnName: str = Field(..., description="新しい列名")
    transformMethod: str = Field(..., description="変換メソッド")
    logBase: Optional[float] = Field(None, description="対数の底（オプション）")
    exponent: Optional[float] = Field(None, description="指数（オプション）")
    rootIndex: Optional[float] = Field(
        None,
        description="累乗根の次数（オプション）"
    )


class GetColumnListRequest(BaseModel):
    """カラムリスト取得リクエスト（GETクエリパラメータ用）"""
    tableName: str = Field(..., description="対象テーブル名")
    isNumberOnly: str = Field(default="false", description="数値カラムのみ取得")

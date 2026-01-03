"""カラム操作関連のスキーマ定義"""
from pydantic import Field
from typing import Optional, List, Dict
from .common import TableRequest, ColumnRequest


class AddColumnRequest(TableRequest):
    """カラム追加リクエスト"""
    newColumnName: str = Field(..., description="新しいカラム名")
    addPositionColumn: str = Field(..., description="追加位置の基準となるカラム名")


class DeleteColumnRequest(ColumnRequest):
    """カラム削除リクエスト"""
    pass


class RenameColumnRequest(TableRequest):
    """カラム名変更リクエスト"""
    oldColumnName: str = Field(..., description="元のカラム名")
    newColumnName: str = Field(..., description="新しいカラム名")


class DuplicateColumnRequest(ColumnRequest):
    """カラム複製リクエスト"""
    newColumnName: str = Field(..., description="新しいカラム名")
    addPositionColumn: str = Field(..., description="追加位置の基準となるカラム名")


class CalculateColumnRequest(TableRequest):
    """カラム計算リクエスト"""
    formula: str = Field(..., description="計算式")
    newColumnName: str = Field(..., description="結果を格納するカラム名")


class GetColumnListRequest(TableRequest):
    """カラムリスト取得リクエスト"""
    pass


class AddDummyColumnRequest(TableRequest):
    """ダミー変数カラム追加リクエスト"""
    sourceColumnName: str = Field(..., description="元となるカラム名")
    dummyColumnName: str = Field(..., description="ダミー変数カラム名")
    targetValue: str = Field(..., description="1にする対象の値")


class AddLagLeadColumnRequest(TableRequest):
    """ラグ・リードカラム追加リクエスト"""
    sourceColumn: str = Field(..., description="元となるカラム名")
    newColumnName: str = Field(..., description="新しいカラム名")
    periods: int = Field(..., description="ラグ・リード期間")
    groupColumns: List[str] = Field(default_factory=list, description="グループ化するカラムのリスト")


class AddSimulationColumnRequest(TableRequest):
    """シミュレーションカラム追加リクエスト"""
    newColumnName: str = Field(..., description="新しいカラム名")
    distributionType: str = Field(..., description="分布の種類")
    distributionParams: dict = Field(..., description="分布のパラメータ")


class SortColumnsRequest(TableRequest):
    """カラムソートリクエスト"""
    sortColumns: List[Dict[str, str]] = Field(..., description="ソート設定のリスト")


class TransformColumnRequest(TableRequest):
    """カラム変換リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    sourceColumnName: str = Field(..., description="元となるカラム名")
    newColumnName: str = Field(..., description="新しい列名")
    transformMethod: str = Field(..., description="変換メソッド")
    logBase: Optional[float] = Field(None, description="対数の底（オプション）")
    exponent: Optional[float] = Field(None, description="指数（オプション）")
    rootIndex: Optional[float] = Field(None, description="累乗根の次数（オプション）")

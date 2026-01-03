"""データ操作・分析関連のスキーマ定義"""
from pydantic import BaseModel, Field
from typing import List, Optional
from .common import TableRequest


class DeleteTableRequest(TableRequest):
    """テーブル削除リクエスト"""
    pass


class DuplicateTableRequest(BaseModel):
    """テーブル複製リクエスト"""
    tableName: str = Field(..., description="元のテーブル名")
    newTableName: str = Field(..., description="新しいテーブル名")


class DuplicateColumnRequest(TableRequest):
    """カラム複製リクエスト"""
    sourceColumnName: str = Field(..., description="元のカラム名")
    newColumnName: str = Field(..., description="新しいカラム名")


class DescriptiveStatisticsRequest(TableRequest):
    """記述統計リクエスト"""
    columnNameList: List[str] = Field(..., description="対象カラム名のリスト")
    statistics: List[str] = Field(..., description="統計量のリスト")


class FilterSingleConditionRequest(BaseModel):
    """単一条件フィルタリクエスト"""
    newTableName: str = Field(..., description="新しいテーブル名")
    tableName: str = Field(..., description="元のテーブル名")
    columnName: str = Field(..., description="対象カラム名")
    condition: str = Field(..., description="条件")
    isCompareColumn: str = Field(..., description="比較対象がカラムかどうか")
    compareValue: str = Field(..., description="比較値")


class FixedEffectsEstimationRequest(TableRequest):
    """固定効果推定リクエスト"""
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(..., description="説明変数の列名リスト")
    entityIdColumn: str = Field(..., description="個体ID列名")
    standardErrorMethod: str = Field(default="normal", description="標準誤差計算方法")
    useTDistribution: bool = Field(default=True, description="t分布を使用するか")

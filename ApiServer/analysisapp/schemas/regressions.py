"""回帰分析関連のスキーマ定義"""
from typing import List

from pydantic import BaseModel, Field


class LinearRegressionRequest(BaseModel):
    """線形回帰リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(
        ...,
        description="説明変数の列名リスト"
    )


class LogisticRegressionRequest(BaseModel):
    """ロジスティック回帰リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(
        ...,
        description="説明変数の列名リスト"
    )


class ProbitRegressionRequest(BaseModel):
    """プロビット回帰リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(
        ...,
        description="説明変数の列名リスト"
    )


class VariableEffectsEstimationRequest(BaseModel):
    """変量効果推定リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(
        ...,
        description="説明変数の列名リスト"
    )
    standardErrorMethod: str = Field(
        default="nonrobust",
        description="標準誤差計算方法"
    )
    useTDistribution: bool = Field(default=True, description="t分布を使用するか")


class FixedEffectsEstimationRequest(BaseModel):
    """固定効果推定リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(
        ...,
        description="説明変数の列名リスト"
    )
    entityIdColumn: str = Field(..., description="個体ID列名")
    standardErrorMethod: str = Field(
        default="normal",
        description="標準誤差計算方法"
    )
    useTDistribution: bool = Field(default=True, description="t分布を使用するか")

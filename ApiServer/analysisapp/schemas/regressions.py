"""回帰分析関連のスキーマ定義"""
from pydantic import Field
from typing import List
from .common import TableRequest


class LinearRegressionRequest(TableRequest):
    """線形回帰リクエスト"""
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(..., description="説明変数の列名リスト")


class LogisticRegressionRequest(TableRequest):
    """ロジスティック回帰リクエスト"""
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(..., description="説明変数の列名リスト")


class ProbitRegressionRequest(TableRequest):
    """プロビット回帰リクエスト"""
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(..., description="説明変数の列名リスト")


class VariableEffectsEstimationRequest(TableRequest):
    """変量効果推定リクエスト"""
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(..., description="説明変数の列名リスト")
    standardErrorMethod: str = Field(default="nonrobust", description="標準誤差計算方法")
    useTDistribution: bool = Field(default=True, description="t分布を使用するか")


class FixedEffectsEstimationRequest(TableRequest):
    """固定効果推定リクエスト"""
    dependentVariable: str = Field(..., description="被説明変数の列名")
    explanatoryVariables: List[str] = Field(..., description="説明変数の列名リスト")
    entityIdColumn: str = Field(..., description="個体ID列名")
    standardErrorMethod: str = Field(default="normal", description="標準誤差計算方法")
    useTDistribution: bool = Field(default=True, description="t分布を使用するか")

"""回帰分析関連のスキーマ定義"""
from typing import List, Dict, Any, Optional, Literal

from pydantic import BaseModel, Field, model_validator


# 統合リクエストスキーマ
class RegressionRequest(BaseModel):
    """
    統合回帰分析リクエスト

    全ての回帰分析タイプを単一のエンドポイントで扱うための
    統合スキーマです。
    """
    type: Literal[
        'ols', 'logit', 'probit', 'tobit',
        'fe', 're', 'iv', 'feiv', 'lasso', 'ridge'
    ] = Field(..., description="分析タイプ")

    method: Literal['ols', 'wls', 'gls', 'gmm'] = Field(
        default='ols',
        description="計算手法"
    )

    tableName: str = Field(..., description="対象テーブル名")

    name: str = Field(
        default="",
        description="分析結果の名前（ユーザー指定）"
    )

    description: str = Field(
        default="",
        description="分析結果の説明・メモ（ユーザー指定）"
    )

    dependentVariable: str = Field(..., description="被説明変数の列名")

    explanatoryVariables: List[str] = Field(
        ...,
        description="説明変数の列名リスト"
    )

    standardErrorMethod: Literal[
        'nonrobust', 'hc0', 'hc1', 'hc2', 'hc3', 'hac', 'clustered'
    ] = Field(
        default='nonrobust',
        description="標準誤差計算方法"
    )

    standardErrorParams: Dict[str, Any] = Field(
        default_factory=dict,
        description="標準誤差計算のパラメータ (例: クラスタ変数名)"
    )

    hyperParameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="ハイパーパラメータ (例: Lasso/Ridge の alpha)"
    )

    useTDistribution: bool = Field(
        default=True,
        description="t分布を使用するか"
    )

    hasConst: bool = Field(
        default=True,
        description="定数項を追加するか"
    )

    missingValueHandling: Literal['ignore', 'remove', 'error'] = Field(
        default='remove',
        description="欠損値の処理方法"
    )

    # パネルデータ分析用
    entityIdColumn: Optional[str] = Field(
        None,
        description="個体ID列名 (固定効果・変量効果の場合に必要)"
    )

    timeColumn: Optional[str] = Field(
        None,
        description="時間列名 (パネルデータ分析の場合に使用)"
    )

    # 操作変数法用
    instrumentalVariables: Optional[List[str]] = Field(
        None,
        description="操作変数の列名リスト (IV の場合に必要)"
    )

    endogenousVariables: Optional[List[str]] = Field(
        None,
        description="内生変数の列名リスト (IV の場合に必要)"
    )

    # Tobit 分析用
    leftCensoringLimit: Optional[float] = Field(
        None,
        description="左側打ち切り値 (Tobit の場合に使用、デフォルト0.0)"
    )

    rightCensoringLimit: Optional[float] = Field(
        None,
        description="右側打ち切り値 (Tobit の場合に使用)"
    )

    @model_validator(mode='after')
    def validate_analysis_params(self):
        """
        分析パラメータの整合性をバリデーション
        """
        # GMM の制限: type="iv" のみ許可
        if self.method == 'gmm' and self.type != 'iv':
            raise ValueError(
                "method='gmm' は type='iv' の場合のみ使用できます"
            )

        # 標準誤差の検証: clustered の場合 groups が必要
        if self.standardErrorMethod == 'clustered':
            # パネルデータの場合はentityIdColumnをデフォルトのgroups として使用
            if self.type in ['fe', 're'] and self.entityIdColumn:
                # standardErrorParamsにgroupsがない場合、entityIdColumnを設定
                if 'groups' not in self.standardErrorParams:
                    self.standardErrorParams['groups'] = self.entityIdColumn
            elif 'groups' not in self.standardErrorParams:
                # パネルデータ以外ではgroupsが必須
                raise ValueError(
                    "standardErrorMethod='clustered' の場合、"
                    "standardErrorParams に 'groups' "
                    "(クラスタ変数名) が必要です"
                )

        # 正則化の検証: lasso, ridge の場合 alpha が必要
        if self.type in ['lasso', 'ridge']:
            if 'alpha' not in self.hyperParameters:
                raise ValueError(
                    f"type='{self.type}' の場合、"
                    "hyperParameters に 'alpha' が必要です"
                )

        # パネルデータ分析の検証
        if self.type in ['fe', 're', 'feiv']:
            if not self.entityIdColumn:
                raise ValueError(
                    f"type='{self.type}' の場合、"
                    "entityIdColumn が必要です"
                )

        # 操作変数法の検証
        if self.type in ['iv', 'feiv']:
            if not self.instrumentalVariables:
                raise ValueError(
                    f"type='{self.type}' の場合、"
                    "instrumentalVariables が必要です"
                )

        return self

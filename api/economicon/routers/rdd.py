"""
回帰不連続デザイン（RDD）分析エンドポイント

rdrobust による RDD 推定・密度検定・プラシーボ検定を提供します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    SuccessResponse,
)
from economicon.schemas.rdd import RDDRequestBody, RDDResult
from economicon.services.data.dependencies import (
    AnalysisResultStoreDep,
    TablesStoreDep,
)
from economicon.services.operation import run_operation
from economicon.services.rdd.rdd_analysis import RDDAnalysis
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post("/rdd", response_model=SuccessResponse[RDDResult])
async def rdd_analysis(
    request: Request,
    body: RDDRequestBody,
    tables_store: TablesStoreDep,
    result_store: AnalysisResultStoreDep,
):
    """
    回帰不連続デザイン（RDD）分析エンドポイント

    rdrobust による局所多項式推定で RDD の LATE を推定します。
    バイアス補正済み推定・McCrary 密度検定・プラシーボ検定を包括的に返します。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : RDDRequestBody
        RDD 分析リクエスト
        - tableName: 対象テーブル名
        - outcomeVariable: 結果変数
        - runningVariable: 実行変数（強制変数）
        - cutoff: カットオフ値（デフォルト: 0）
        - kernel: カーネル関数 ('triangular' / 'epanechnikov' / 'uniform')
        - bwSelect: バンド幅自動選択アルゴリズム
        - h: 手動バンド幅（null の場合は自動選択）
        - p: 多項式次数（1: 線形, 2: 2次式）
        - vce: 標準誤差の計算方法
        - confidenceLevel: 信頼区間水準（デフォルト: 0.95）
        - nBins: 散布図用ビン数（デフォルト: 30）
        - placeboCutoffs: プラシーボ境界値リスト（null で自動生成）

    Returns
    -------
    JSONResponse
        {"code": "OK", "result": {"resultId": "<uuid>"}}
        分析結果は GET /analysis/results/{resultId} で取得可能。
    """
    api = RDDAnalysis(body, tables_store, result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

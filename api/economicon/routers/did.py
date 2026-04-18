"""
差の差（DID）分析エンドポイント

TWFE（Two-Way Fixed Effects）に基づく DID 推定と
オプションの Event Study を提供します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    DIDResult,
    SuccessResponse,
)
from economicon.schemas.did import DIDRequestBody
from economicon.services.data.dependencies import (
    AnalysisResultStoreDep,
    TablesStoreDep,
)
from economicon.services.did.did_analysis import DIDAnalysis
from economicon.services.operation import run_operation
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post("/did", response_model=SuccessResponse[DIDResult])
async def did_analysis(
    request: Request,
    body: DIDRequestBody,
    tables_store: TablesStoreDep,
    result_store: AnalysisResultStoreDep,
):
    """
    差の差（DID）分析エンドポイント

    Two-Way Fixed Effects（TWFE）による DID 推定を実行します。
    交差項（treated × post）はサービス層で自動生成されます。
    include_event_study=true の場合、各時点の処置効果係数も推定します。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : DIDRequestBody
        DID 分析リクエスト
        - tableName: 対象テーブル名
        - dependentVariable: 被説明変数
        - treatmentColumn: 処置群ダミー（treated_i）
        - postColumn: 処置後ダミー（post_t）
        - timeColumn: 時点列
        - entityIdColumn: 個体 ID 列
        - explanatoryVariables: 追加共変量（省略可）
        - includeEventStudy: Event Study 実行フラグ
        - basePeriod: Event Study 基準期（省略時は自動選択）
        - standardError: 標準誤差の種別（cluster 推奨）
        - confidenceLevel: 信頼区間水準

    Returns
    -------
    JSONResponse
        {"code": "OK", "result": {"resultId": "<uuid>"}}
        分析結果は GET /analysis/results/{resultId} で取得可能。
    """
    api = DIDAnalysis(body, tables_store, result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

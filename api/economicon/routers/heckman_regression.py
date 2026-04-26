"""
ヘックマン2段階推定エンドポイント

Probit（選択方程式）+ OLS + IMR（結果方程式）の
2段階推定によりサンプルセレクションバイアスを補正します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    HeckmanResult,
    SuccessResponse,
)
from economicon.schemas.heckman import HeckmanRequestBody
from economicon.services.data.dependencies import (
    AnalysisResultStoreDep,
    TablesStoreDep,
)
from economicon.services.operation import run_operation
from economicon.services.selection_models import HeckmanRegression
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post(
    "/heckman-regression",
    response_model=SuccessResponse[HeckmanResult],
)
async def heckman_regression(
    request: Request,
    body: HeckmanRequestBody,
    tables_store: TablesStoreDep,
    result_store: AnalysisResultStoreDep,
):
    """
    ヘックマン2段階推定エンドポイント

    Step 1 で Probit により選択方程式を推定し逆ミルズ比 (IMR)
    を計算します。Step 2 で IMR を追加した OLS により結果方程式
    を推定し、セレクションバイアスを補正します。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : HeckmanRequestBody
        - tableName: 対象テーブル名
        - dependentVariable: 被説明変数（結果方程式）
        - explanatoryVariables: 説明変数（結果方程式）
        - selectionColumn: 選択ダミー列（0/1）
        - selectionVariables: 説明変数（選択方程式）
        - reportFirstStage: 第1段階結果を含めるか

    Returns
    -------
    JSONResponse
        分析結果 ID またはエラーメッセージ
    """
    api = HeckmanRegression(body, tables_store, result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK,
        response_object=result,
    )

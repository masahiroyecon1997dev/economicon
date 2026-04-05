"""
統合回帰分析エンドポイント

全ての回帰分析タイプを単一のエンドポイントで処理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    AddDiagnosticColumnsResult,
    RegressionResult,
    SuccessResponse,
)
from economicon.schemas.regressions import (
    AddDiagnosticColumnsRequestBody,
    RegressionRequestBody,
)
from economicon.services.data.dependencies import (
    AnalysisResultStoreDep,
    TablesStoreDep,
)
from economicon.services.operation import run_operation
from economicon.services.regressions.add_diagnostic_columns import (
    AddDiagnosticColumns,
)
from economicon.services.regressions.factory import create_regression
from economicon.utils import (
    create_success_response,
)

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post("/regression", response_model=SuccessResponse[RegressionResult])
async def regression(
    request: Request,
    body: RegressionRequestBody,
    tables_store: TablesStoreDep,
    result_store: AnalysisResultStoreDep,
):
    """
    統合回帰分析エンドポイント

    typeフィールドに応じて適切な分析手法を選択し、実行します。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RegressionRequestBody
        統合回帰分析リクエスト
        - type: 分析タイプ (ols, logit, probit, tobit, fe, re, iv,
          feiv, lasso, ridge)
        - tableName: 対象テーブル名
        - dependentVariable: 被説明変数
        - explanatoryVariables: 説明変数のリスト
        - その他分析固有のパラメータ

    Returns
    -------
    JSONResponse
        分析結果またはエラーメッセージ
    """
    # ビジネスロジックの実行
    api = create_regression(body, tables_store, result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/regression/add-diagnostic-columns",
    response_model=SuccessResponse[AddDiagnosticColumnsResult],
)
async def add_diagnostic_columns(
    request: Request,
    body: AddDiagnosticColumnsRequestBody,
    tables_store: TablesStoreDep,
    result_store: AnalysisResultStoreDep,
):
    """
    推定済みモデルから予測値・残差を抽出してテーブルに列追加する

    指定された分析結果 ID に対応するモデルをロードし、予測値・残差などの
    診断列を元のテーブルに追加します。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : AddDiagnosticColumnsRequestBody
        - tableName: 追加先テーブル名
        - resultId: 分析結果の UUID
        - target: "fitted" / "residual" / "both"
        - standardized: 標準化残差を含めるか（OLS 系のみ有効）
        - includeInterval: 95%信頼区間を含めるか
        - feType: "total" または "within"（FE/RE のみ有効）

    Returns
    -------
    JSONResponse
        追加したテーブル名と列名リスト
    """
    api = AddDiagnosticColumns(body, tables_store, result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

"""
統合回帰分析エンドポイント

全ての回帰分析タイプを単一のエンドポイントで処理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    AddDiagnosticColumnsResult,
    ClearAllAnalysisResultsResult,
    DeleteAnalysisResultResult,
    GetAllAnalysisResultsResult,
    GetAnalysisResultResult,
    OutputResultResult,
    RegressionResult,
    SuccessResponse,
)
from economicon.schemas.regressions import (
    AddDiagnosticColumnsRequestBody,
    OutputResultRequest,
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
from economicon.services.regressions.output_result import OutputResult
from economicon.services.regressions.result import (
    ClearAllAnalysisResults,
    DeleteAnalysisResult,
    GetAllAnalysisResults,
    GetAnalysisResult,
)
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


@router.get(
    "/results", response_model=SuccessResponse[GetAllAnalysisResultsResult]
)
async def get_all_analysis_results(
    request: Request,
    result_store: AnalysisResultStoreDep,
):
    """
    すべての分析結果のサマリーを取得

    Returns
    -------
    JSONResponse
        分析結果のサマリーリスト
    """
    # ビジネスロジックの実行
    api = GetAllAnalysisResults(result_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.get(
    "/results/{result_id}",
    response_model=SuccessResponse[GetAnalysisResultResult],
)
async def get_analysis_result(
    request: Request,
    result_id: str,
    result_store: AnalysisResultStoreDep,
):
    """
    指定されたIDの分析結果を取得

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    result_id : str
        結果のID

    Returns
    -------
    JSONResponse
        分析結果の詳細
    """
    # ビジネスロジックの実行
    api = GetAnalysisResult(result_id, result_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.delete(
    "/results/{result_id}",
    response_model=SuccessResponse[DeleteAnalysisResultResult],
)
async def delete_analysis_result(
    request: Request,
    result_id: str,
    result_store: AnalysisResultStoreDep,
):
    """
    指定されたIDの分析結果を削除

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    result_id : str
        削除する結果のID

    Returns
    -------
    JSONResponse
        削除成功メッセージ
    """
    # ビジネスロジックの実行
    api = DeleteAnalysisResult(result_id, result_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.delete(
    "/results", response_model=SuccessResponse[ClearAllAnalysisResultsResult]
)
async def clear_all_analysis_results(
    request: Request,
    result_store: AnalysisResultStoreDep,
):
    """
    すべての分析結果を削除

    Returns
    -------
    JSONResponse
        削除成功メッセージ
    """
    # ビジネスロジックの実行
    api = ClearAllAnalysisResults(result_store)
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


@router.post(
    "/output-result",
    response_model=SuccessResponse[OutputResultResult],
)
async def output_result(
    request: Request,
    body: OutputResultRequest,
    result_store: AnalysisResultStoreDep,
):
    """
    推定結果をテキスト / Markdown / LaTeX 形式で整形出力する

    指定した分析結果 ID のリストから係数表などを生成します。
    複数 ID を指定するとモデル比較表を生成します。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : OutputResultRequest
        - resultIds: 出力する分析結果 ID のリスト（1件以上）
        - format: 出力形式（text / markdown / latex）
        - statInParentheses: 括弧内統計量（se / t / p / none）
        - significanceStars: 有意性記号の設定（省略時はデフォルト）
        - variableLabels: 変数名の表示ラベル辞書
        - constAtBottom: 定数項を最下部に表示するか

    Returns
    -------
    JSONResponse
        整形済み出力テキストを含む成功レスポンス
    """
    api = OutputResult(body, result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

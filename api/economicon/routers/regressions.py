"""
統合回帰分析エンドポイント

全ての回帰分析タイプを単一のエンドポイントで処理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..exceptions import ApiError
from ..models.regressions import RegressionRequestBody
from ..services.operation import run_operation
from ..services.regressions.regression import Regression
from ..services.regressions.result import (
    ClearAllAnalysisResults,
    DeleteAnalysisResult,
    GetAllAnalysisResults,
    GetAnalysisResult,
)
from ..utils import (
    create_error_response,
    create_log_api_request,
    create_success_response,
)
from ..utils.validators.common import ValidationError

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/regression")
async def regression(request: Request, body: RegressionRequestBody):
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
    create_log_api_request(request)
    api = Regression(**body.model_dump())
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.get("/results")
async def get_all_analysis_results(request: Request):
    """
    すべての分析結果のサマリーを取得

    Returns
    -------
    JSONResponse
        分析結果のサマリーリスト
    """
    create_log_api_request(request)

    try:
        # リクエスト受け取りログ
        create_log_api_request(request)
        # ビジネスロジックの実行
        api = GetAllAnalysisResults()
        result = run_operation(api)

        return create_success_response(http_status.HTTP_200_OK, result)

    except ValidationError as e:
        return create_error_response(http_status.HTTP_400_BAD_REQUEST, str(e))
    except ApiError as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)
        )
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}",
        )


@router.get("/results/{result_id}")
async def get_analysis_result(request: Request, result_id: str):
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
    create_log_api_request(request)

    try:
        api = GetAnalysisResult(result_id)
        result = run_operation(api)

        return create_success_response(http_status.HTTP_200_OK, result)

    except ValidationError as e:
        return create_error_response(http_status.HTTP_400_BAD_REQUEST, str(e))
    except ApiError as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)
        )
    except KeyError as e:
        return create_error_response(http_status.HTTP_404_NOT_FOUND, str(e))
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}",
        )


@router.delete("/results/{result_id}")
async def delete_analysis_result(request: Request, result_id: str):
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
    create_log_api_request(request)

    try:
        api = DeleteAnalysisResult(result_id)
        result = run_operation(api)

        return create_success_response(http_status.HTTP_200_OK, result)

    except ValidationError as e:
        return create_error_response(http_status.HTTP_400_BAD_REQUEST, str(e))
    except ApiError as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)
        )
    except KeyError as e:
        return create_error_response(http_status.HTTP_404_NOT_FOUND, str(e))
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}",
        )


@router.delete("/results")
async def clear_all_analysis_results(request: Request):
    """
    すべての分析結果を削除

    Returns
    -------
    JSONResponse
        削除成功メッセージ
    """
    create_log_api_request(request)

    try:
        api = ClearAllAnalysisResults()
        result = run_operation(api)

        return create_success_response(http_status.HTTP_200_OK, result)

    except ValidationError as e:
        return create_error_response(http_status.HTTP_400_BAD_REQUEST, str(e))
    except ApiError as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)
        )
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}",
        )

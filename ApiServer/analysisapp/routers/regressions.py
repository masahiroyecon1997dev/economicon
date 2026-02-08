"""
統合回帰分析エンドポイント

全ての回帰分析タイプを単一のエンドポイントで処理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..schemas.regressions import RegressionRequest
from ..services.abstract_api import ApiError
from ..services.regressions.regression import regression
from ..services.regressions.result import (
    clear_all_analysis_results,
    delete_analysis_result,
    get_all_analysis_results,
    get_analysis_result,
)
from ..utils import (
    create_error_response,
    create_log_api_request,
    create_success_response,
)
from ..utils.validators.common_validators import ValidationError

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/regression")
async def regression_endpoint(request: Request, body: RegressionRequest):
    """
    統合回帰分析エンドポイント

    typeフィールドに応じて適切な分析手法を選択し、実行します。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RegressionRequest
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
    result = regression(**body.model_dump())
    return create_success_response(http_status.HTTP_200_OK, result)


@router.get("/results")
async def get_all_analysis_results_endpoint(request: Request):
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
        # ビジネスロジックの実行（既存のpython_apisをそのまま使用）
        result = get_all_analysis_results()

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
async def get_analysis_result_endpoint(request: Request, result_id: str):
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
        result = get_analysis_result(result_id)

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
async def delete_analysis_result_endpoint(request: Request, result_id: str):
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
        result = delete_analysis_result(result_id)

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
async def clear_all_analysis_results_endpoint(request: Request):
    """
    すべての分析結果を削除

    Returns
    -------
    JSONResponse
        削除成功メッセージ
    """
    create_log_api_request(request)

    try:
        result = clear_all_analysis_results()

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

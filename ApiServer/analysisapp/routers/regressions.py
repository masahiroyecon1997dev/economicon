"""
統合回帰分析エンドポイント

全ての回帰分析タイプを単一のエンドポイントで処理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..schemas.regressions import RegressionRequest
from ..services.regression import execute_regression_analysis
from ..utils.validator.common_validators import ValidationError
from ..services.abstract_api import ApiError
from ..utils import (
    create_log_api_request,
    create_success_response,
    create_error_response
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/regression")
async def unified_regression_endpoint(
    request: Request,
    body: RegressionRequest
):
    """
    統合回帰分析エンドポイント

    typeフィールドに応じて適切な分析手法を選択し、実行します。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AnalysisRequest
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

    try:
        # 共通パラメータの準備
        params = {
            'analysis_type': body.type,
            'table_name': body.tableName,
            'dependent_variable': body.dependentVariable,
            'explanatory_variables': body.explanatoryVariables,
            'standard_error_method': body.standardErrorMethod,
            'has_const': body.hasConst,
            'missing_value_handling': body.missingValueHandling,
            'use_t_distribution': body.useTDistribution,
        }

        # パネルデータパラメータ
        if body.entityIdColumn:
            params['entity_id_column'] = body.entityIdColumn
        if body.timeColumn:
            params['time_column'] = body.timeColumn

        # 操作変数パラメータ
        if body.instrumentalVariables:
            params['instrumental_variables'] = body.instrumentalVariables
        if body.endogenousVariables:
            params['endogenous_variables'] = body.endogenousVariables

        # Tobitパラメータ
        if body.leftCensoringLimit is not None:
            params['left_censoring_limit'] = body.leftCensoringLimit
        if body.rightCensoringLimit is not None:
            params['right_censoring_limit'] = body.rightCensoringLimit

        # 正則化パラメータ
        if 'alpha' in body.hyperParameters:
            params['alpha'] = body.hyperParameters['alpha']

        # 統合サービスを呼び出し
        result = execute_regression_analysis(**params)

        return create_success_response(
            http_status.HTTP_200_OK,
            result
        )

    except ValidationError as e:
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST,
            str(e)
        )
    except ApiError as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            str(e)
        )
    except NotImplementedError as e:
        return create_error_response(
            http_status.HTTP_501_NOT_IMPLEMENTED,
            str(e)
        )
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )

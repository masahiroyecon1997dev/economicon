from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..schemas import (FixedEffectsEstimationRequest, LinearRegressionRequest,
                       LogisticRegressionRequest, ProbitRegressionRequest,
                       VariableEffectsEstimationRequest)
from ..services.fixed_effects_estimation import fixed_effects_estimation
from ..services.linear_regression import linear_regression
from ..services.logistic_regression import logistic_regression
from ..services.probit_regression import probit_regression
from ..services.variable_effects_estimation import variable_effects_estimation
from ..utils import create_log_api_request, create_success_response

router = APIRouter(prefix="/regression", tags=["regression"])


@router.post("/linear")
async def linear_regression_endpoint(request: Request,
                                     body: LinearRegressionRequest):
    """線形回帰分析を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : LinearRegressionRequest
        リクエストボディ
        - tableName: テーブル名
        - dependentVariable: 被説明変数の列名
        - explanatoryVariables: 説明変数の列名リスト

    Returns
    -------
    JSONResponse
        線形回帰分析の結果
    """
    create_log_api_request(request)

    result = linear_regression(
        table_name=body.tableName,
        dependent_variable=body.dependentVariable,
        explanatory_variables=body.explanatoryVariables
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/logistic")
async def logistic_regression_endpoint(request: Request,
                                       body: LogisticRegressionRequest):
    """ロジット分析を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : LogisticRegressionRequest
        リクエストボディ
        - tableName: テーブル名
        - dependentVariable: 被説明変数の列名
        - explanatoryVariables: 説明変数の列名リスト

    Returns
    -------
    JSONResponse
        ロジット分析の結果
    """
    create_log_api_request(request)

    result = logistic_regression(
        table_name=body.tableName,
        dependent_variable=body.dependentVariable,
        explanatory_variables=body.explanatoryVariables
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/probit")
async def probit_regression_endpoint(request: Request,
                                     body: ProbitRegressionRequest):
    """プロビット分析を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ProbitRegressionRequest
        リクエストボディ
        - tableName: テーブル名
        - dependentVariable: 被説明変数の列名
        - explanatoryVariables: 説明変数の列名リスト

    Returns
    -------
    JSONResponse
        プロビット分析の結果
    """
    create_log_api_request(request)

    result = probit_regression(
        table_name=body.tableName,
        dependent_variable=body.dependentVariable,
        explanatory_variables=body.explanatoryVariables
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/variable-effects")
async def variable_effects_estimation_endpoint(
        request: Request, body: VariableEffectsEstimationRequest):
    """変量効果推定分析を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : VariableEffectsEstimationRequest
        リクエストボディ
        - tableName: テーブル名
        - dependentVariable: 被説明変数の列名
        - explanatoryVariables: 説明変数の列名リスト
        - standardErrorMethod: 標準誤差の計算方法（オプション、デフォルト: "nonrobust"）
        - useTDistribution: t分布を使用するか（オプション、デフォルト: true）

    Returns
    -------
    JSONResponse
        変量効果推定分析の結果
    """
    create_log_api_request(request)

    result = variable_effects_estimation(
        table_name=body.tableName,
        dependent_variable=body.dependentVariable,
        explanatory_variables=body.explanatoryVariables,
        standard_error_method=body.standardErrorMethod,
        use_t_distribution=body.useTDistribution
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/fixed-effects")
async def fixed_effects_estimation_endpoint(
        request: Request, body: FixedEffectsEstimationRequest):
    """固定効果推定を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FixedEffectsEstimationRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = fixed_effects_estimation(
        table_name=body.tableName,
        dependent_variable=body.dependentVariable,
        explanatory_variables=body.explanatoryVariables,
        entity_id_column=body.entityIdColumn,
        standard_error_method=body.standardErrorMethod,
        use_t_distribution=body.useTDistribution
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

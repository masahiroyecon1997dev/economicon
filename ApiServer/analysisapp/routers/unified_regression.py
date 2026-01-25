"""
統合回帰分析エンドポイント

全ての回帰分析タイプを単一のエンドポイントで処理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..schemas.regressions import AnalysisRequest
from ..services.regressions import (
    OLSRegression,
    LogitRegression,
    ProbitRegression,
    TobitRegression,
    FixedEffectsRegression,
    RandomEffectsRegression,
    IVRegression,
    LassoRegression,
    RidgeRegression
)
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
    body: AnalysisRequest
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
          lasso, ridge)
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
        # 共通パラメータの抽出（基本的なもの）
        common_params = {
            'table_name': body.tableName,
            'dependent_variable': body.dependentVariable,
            'explanatory_variables': body.explanatoryVariables,
            'standard_error_method': body.standardErrorMethod,
            'missing_value_handling': body.missingValueHandling,
            'use_t_distribution': body.useTDistribution
        }

        # typeに応じてサービスクラスを選択
        match body.type:
            case 'ols':
                api = OLSRegression(**common_params, has_const=body.hasConst)

            case 'logit':
                api = LogitRegression(**common_params, has_const=body.hasConst)

            case 'probit':
                api = ProbitRegression(**common_params, has_const=body.hasConst)

            case 'tobit':
                api = TobitRegression(
                    **common_params,
                    has_const=body.hasConst,
                    left_censoring_limit=body.leftCensoringLimit,
                    right_censoring_limit=body.rightCensoringLimit
                )

            case 'fe':
                if not body.entityIdColumn:
                    return create_error_response(
                        http_status.HTTP_400_BAD_REQUEST,
                        "entityIdColumn is required for fixed effects "
                        "analysis"
                    )
                # パネル分析では has_const は使用しない
                api = FixedEffectsRegression(
                    **common_params,
                    entity_id_column=body.entityIdColumn,
                    time_column=body.timeColumn
                )

            case 're':
                if not body.entityIdColumn:
                    return create_error_response(
                        http_status.HTTP_400_BAD_REQUEST,
                        "entityIdColumn is required for random effects "
                        "analysis"
                    )
                # パネル分析では has_const は使用しない
                api = RandomEffectsRegression(
                    **common_params,
                    entity_id_column=body.entityIdColumn,
                    time_column=body.timeColumn
                )

            case 'iv':
                if not body.instrumentalVariables:
                    return create_error_response(
                        http_status.HTTP_400_BAD_REQUEST,
                        "instrumentalVariables is required for IV analysis"
                    )
                api = IVRegression(
                    **common_params,
                    has_const=body.hasConst,
                    instrumental_variables=body.instrumentalVariables,
                    endogenous_variables=body.endogenousVariables
                )

            case 'lasso':
                if 'alpha' not in body.hyperParameters:
                    return create_error_response(
                        http_status.HTTP_400_BAD_REQUEST,
                        "alpha is required in hyperParameters for "
                        "Lasso regression"
                    )
                api = LassoRegression(
                    **common_params,
                    has_const=body.hasConst,
                    alpha=body.hyperParameters['alpha']
                )

            case 'ridge':
                if 'alpha' not in body.hyperParameters:
                    return create_error_response(
                        http_status.HTTP_400_BAD_REQUEST,
                        "alpha is required in hyperParameters for "
                        "Ridge regression"
                    )
                api = RidgeRegression(
                    **common_params,
                    has_const=body.hasConst,
                    alpha=body.hyperParameters['alpha']
                )

            case _:
                return create_error_response(
                    http_status.HTTP_400_BAD_REQUEST,
                    f"Unknown analysis type: {body.type}"
                )

        # バリデーション実行
        validation_error = api.validate()
        if validation_error:
            return create_error_response(
                http_status.HTTP_400_BAD_REQUEST,
                str(validation_error)
            )

        # 分析実行
        result = api.execute()

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
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )

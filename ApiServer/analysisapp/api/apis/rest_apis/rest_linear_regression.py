from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..python_apis.linear_regression import linear_regression
from ..python_apis.abstract_api import ApiError


class LinearRegression(APIView):
    """
    線形回帰分析を行うREST APIクラス

    POST /api/linear-regression
    {
        "tableName": "テーブル名",
        "dependentVariable": "被説明変数の列名",
        "explanatoryVariables": ["説明変数1", "説明変数2", ...]
    }
    """

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)

            # リクエストデータの取得
            request_data = json.loads(request.body)
            table_name = request_data['tableName']
            dependent_variable = request_data['dependentVariable']
            explanatory_variables = request_data['explanatoryVariables']

            # 線形回帰分析の実行
            result = linear_regression(
                table_name=table_name,
                dependent_variable=dependent_variable,
                explanatory_variables=explanatory_variables
            )

            return create_success_response(
                status.HTTP_200_OK,
                result)

        except ValidationError as e:
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                e.message
            )
        except ApiError as e:
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                e.message
            )
        except KeyError as e:
            message = _("Required parameter is missing: {}").format(str(e))
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message
            )
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "linear regression processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

import json

from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.views import APIView

from ..python_apis.common_api_class import ApiError
from ..python_apis.probit_regression import probit_regression
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (create_error_response,
                                         create_success_response)
from ..utilities.validator.common_validators import ValidationError


class ProbitRegression(APIView):
    """
    プロビット分析を行うREST APIクラス

    POST /api/probit-regression
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

            # プロビット分析の実行
            result = probit_regression(
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
                        "probit regression processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..python_apis.confidence_interval import confidence_interval
from ..python_apis.common_api_class import ApiError


class ConfidenceInterval(APIView):
    """
    信頼区間計算を行うREST APIクラス

    POST /api/confidence_interval
    {
        "tableName": "テーブル名",
        "columnName": "列名", 
        "confidenceLevel": 0.95,
        "statisticType": "mean"
    }
    """

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)

            # リクエストデータの取得
            request_data = json.loads(request.body)
            table_name = request_data['tableName']
            column_name = request_data['columnName']
            confidence_level = request_data['confidenceLevel']
            statistic_type = request_data['statisticType']

            # 信頼区間計算の実行
            result = confidence_interval(
                table_name=table_name,
                column_name=column_name,
                confidence_level=confidence_level,
                statistic_type=statistic_type
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
                        "confidence interval processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )
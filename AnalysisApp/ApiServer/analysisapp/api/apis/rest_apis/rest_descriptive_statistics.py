from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..python_apis.descriptive_statistics import descriptive_statistics
from ..python_apis.common_api_class import ApiError


class DescriptiveStatistics(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            table_name = request_data['tableName']
            column_name = request_data['columnName']
            statistics = request_data['statistics']  # List of statistics to compute
            
            result = descriptive_statistics(
                table_name=table_name,
                column_name=column_name,
                statistics=statistics
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
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "descriptive statistics processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )
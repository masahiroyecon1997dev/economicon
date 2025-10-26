from rest_framework.views import APIView
from rest_framework import status
import json
from ..utilities.create_log import create_log_api_request
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..python_apis.delete_column import delete_column
from ..python_apis.common_api_class import ApiError
from ..utilities.validator.common_validators import ValidationError


class RestDeleteColumn(APIView):
    """
    列削除APIのRESTエンドポイント
    """
    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            table_name = request_data.get('tableName')
            column_name = request_data.get('columnName')
            result = delete_column(table_name, column_name)
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
            message = _(
                "An unexpected error occurred during "
                "column deletion processing"
            )
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

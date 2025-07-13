from rest_framework.views import APIView
from rest_framework import status
import json
from django.utils.translation import gettext as _
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (
    create_success_response,
    create_error_response
)
from ..python_apis.input_cell_data import (
    input_cell_data,
    ValidationError,
    ApiError
)


class RestInputCellData(APIView):
    """
    セルデータ入力APIのRESTエンドポイント
    """
    def post(self, request):
        try:
            create_log_api_request(request)
            request_data = json.loads(request.body)
            table_name = request_data['tableName']
            column_name = request_data['columnName']
            row_index = request_data['rowIndex']
            new_value = request_data['newValue']
            result = input_cell_data(
                table_name,
                column_name,
                row_index,
                new_value
            )
            return create_success_response(status.HTTP_200_OK, result)
        except ValidationError as e:
            return create_error_response(status.HTTP_400_BAD_REQUEST,
                                         e.message)
        except ApiError as e:
            return create_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                         e.message)
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "input cell data processing"
            )
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

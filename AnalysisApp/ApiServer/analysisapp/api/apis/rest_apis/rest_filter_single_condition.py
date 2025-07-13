from rest_framework.views import APIView
from rest_framework import status
import json
from django.utils.translation import gettext as _
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (
    create_success_response,
    create_error_response
)
from ..python_apis.filter_single_condition import (filter_single_condition,
                                                   ValidationError,
                                                   ApiError)


class RestFilterSingleCondition(APIView):
    """
    単一条件フィルタAPIのRESTエンドポイント
    """
    def post(self, request):
        try:
            create_log_api_request(request)
            request_data = json.loads(request.body)
            new_table_name = request_data['newTableName']
            table_name = request_data['tableName']
            column_name = request_data['columnName']
            condition = request_data['condition']
            is_compare_column = request_data['isCompareColumn']
            compare_value = request_data['compareValue']
            result = filter_single_condition(
                new_table_name,
                table_name,
                column_name,
                condition,
                is_compare_column,
                compare_value
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
                "An unexpected error occurred during filter processing"
            )
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

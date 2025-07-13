from rest_framework.views import APIView
from rest_framework import status
import json
from django.utils.translation import gettext as _
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (
    create_success_response,
    create_error_response
)
from ..python_apis.rename_column_name import (
    rename_column_name,
    ValidationError,
    ApiError
)


class RestRenameColumnName(APIView):
    """
    列名変更APIのRESTエンドポイント
    """
    def post(self, request):
        try:
            create_log_api_request(request)
            request_data = json.loads(request.body)
            table_name = request_data['tableName']
            old_column_name = request_data['oldColumnName']
            new_column_name = request_data['newColumnName']
            result = rename_column_name(
                table_name,
                old_column_name,
                new_column_name
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
                "renaming column processing"
            )
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

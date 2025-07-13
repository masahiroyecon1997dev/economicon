from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (
    create_success_response,
    create_error_response,
)
from ..utilities.create_log import create_log_api_request
from ..python_apis.delete_table import delete_table
from ..python_apis.common_api_class import ApiError
from ..utilities.validator.common_validators import ValidationError


class DeleteTable(APIView):

    def post(self, request):
        try:
            create_log_api_request(request)
            request_data = json.loads(request.body)
            table_name = request_data['tableName']
            result = delete_table(table_name=table_name)
            return create_success_response(
                status.HTTP_200_OK,
                result
            )
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
                "An unexpected error occurred during table deletion processing"
            )
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

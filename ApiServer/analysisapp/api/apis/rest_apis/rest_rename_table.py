from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (
    create_success_response,
    create_error_response,
)
from ..utilities.create_log import create_log_api_request
from ..python_apis.rename_table_name import rename_table
from ..python_apis.common_api_class import ApiError
from ..utilities.validator.common_validators import ValidationError


class RenameTable(APIView):

    def post(self, request):
        try:
            create_log_api_request(request)
            request_data = json.loads(request.body)
            old_table_name = request_data.get('oldTableName')
            new_table_name = request_data.get('newTableName')
            result = rename_table(
                old_table_name=old_table_name,
                new_table_name=new_table_name,
            )
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
                "An unexpected error occurred during table rename processing"
            )
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

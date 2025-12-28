from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.create_log import create_log_api_request
from ..python_apis.create_table import create_table
from ..python_apis.abstract_api import ApiError
from ..utilities.validator.common_validators import ValidationError


class CreateTable(APIView):
    def post(self, request):
        try:
            create_log_api_request(request)
            request_data = json.loads(request.body)
            table_name = request_data.get('tableName')
            table_number_of_rows = request_data.get('tableNumberOfRows')
            columnNames = request_data.get('columnNames')
            result = create_table(
                table_name,
                table_number_of_rows,
                columnNames
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
                        "table creation processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

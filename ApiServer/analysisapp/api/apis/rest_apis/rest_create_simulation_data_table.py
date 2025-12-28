import json

from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.views import APIView

from ..python_apis.abstract_api import ApiError
from ..python_apis.create_simulation_data_table import \
    create_simulation_data_table
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (create_error_response,
                                         create_success_response)
from ..utilities.validator.common_validators import ValidationError


class CreateSimulationDataTable(APIView):
    def post(self, request):
        try:
            create_log_api_request(request)
            request_data = json.loads(request.body)
            table_name = request_data.get('tableName')
            table_number_of_rows = request_data.get('tableNumberOfRows')
            column_settings = request_data.get('columnSettings')
            result = create_simulation_data_table(
                table_name,
                table_number_of_rows,
                column_settings
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

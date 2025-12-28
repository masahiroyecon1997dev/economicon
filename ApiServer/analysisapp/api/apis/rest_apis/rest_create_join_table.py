from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.create_log import create_log_api_request
from ..python_apis.create_join_table import create_join_table
from ..python_apis.abstract_api import ApiError
from ..utilities.validator.common_validators import ValidationError


class CreateJoinTable(APIView):
    def post(self, request):
        try:
            create_log_api_request(request)
            request_data = json.loads(request.body)
            join_table_name = request_data.get('joinTableName')
            left_table_name = request_data.get('leftTableName')
            right_table_name = request_data.get('rightTableName')
            left_key_column_names = request_data.get('leftKeyColumnNames')
            right_key_column_names = request_data.get('rightKeyColumnNames')
            join_type = request_data.get('joinType')
            result = create_join_table(
                join_table_name=join_table_name,
                left_table_name=left_table_name,
                right_table_name=right_table_name,
                left_key_column_names=left_key_column_names,
                right_key_column_names=right_key_column_names,
                join_type=join_type
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
                        "join table creation processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

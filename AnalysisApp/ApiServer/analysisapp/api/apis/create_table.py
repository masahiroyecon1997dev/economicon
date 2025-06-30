from rest_framework import status
from rest_framework.views import APIView
import polars as pl
import json
from django.utils.translation import gettext as _
from .utilities.create_response import (create_success_response,
                                        create_error_response)
from .utilities.create_log import create_log_api_request
from .utilities.validator.input_request_validators import (
    validate_add_column_request
)
from .data.tables_info import all_tables_info


class CreateTable(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # バリデーション
            validation_error = validate_add_column_request(request)
            if validation_error:
                return validation_error

        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding column processing")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                e
            )

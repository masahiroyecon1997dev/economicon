from rest_framework import status
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.create_log import create_log_api_request
from ..python_apis.clear_tables import clear_tables
from ..python_apis.common_api_class import ApiError


class ClearTables(APIView):

    def delete(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # パラメータなしでテーブルをクリア
            result = clear_tables()
            return create_success_response(
                status.HTTP_200_OK,
                result)

        except ApiError as e:
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                e.message
            )
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "clearing tables processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

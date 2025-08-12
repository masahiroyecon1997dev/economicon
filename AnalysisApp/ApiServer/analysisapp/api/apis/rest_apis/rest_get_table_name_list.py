from rest_framework import status
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.create_log import create_log_api_request
from ..python_apis.get_table_name_list import get_table_name_list
from ..python_apis.common_api_class import ApiError


class GetTableNameList(APIView):
    """GetTableNameList API class

    すべてのテーブル名を取得します。
    """
    def get(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            result = get_table_name_list()
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
                        "getting table name list processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

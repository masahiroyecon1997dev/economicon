from rest_framework import status
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..python_apis.fetch_data_to_json import fetch_data_to_json
from ..python_apis.abstract_api import ApiError


class FetchDataToJson(APIView):
    """FetchDataToJson API class

    指定されたテーブルの指定された行範囲のデータをJSON形式で取得します。
    行番号は1から始まると仮定しています。
    """
    def get(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            table_name = request.query_params.get('tableName')
            firstRow = request.query_params.get('firstRow')
            lastRow = request.query_params.get('lastRow')
            result = fetch_data_to_json(
                table_name=table_name,
                first_row=firstRow,
                last_row=lastRow
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
                        "fetching data processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

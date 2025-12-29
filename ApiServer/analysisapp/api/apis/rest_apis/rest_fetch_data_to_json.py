from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.views import APIView

from ..python_apis.abstract_api import ApiError
from ..python_apis.fetch_data_to_json import fetch_data_to_json
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (create_error_response,
                                         create_success_response)
from ..utilities.validator.common_validators import ValidationError


class FetchDataToJson(APIView):
    """FetchDataToJson API class

    指定されたテーブルの指定された開始行から指定された行数のデータをJSON形式で取得します。
    行番号は1から始まると仮定しています。
    取得行数がテーブルの行数を超える場合は、テーブルの最後まで取得します。
    """
    def get(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            table_name = request.query_params.get('tableName')
            start_row = request.query_params.get('startRow')
            fetch_rows = request.query_params.get('fetchRows')

            result = fetch_data_to_json(
                table_name=table_name,
                start_row=start_row,
                fetch_rows=fetch_rows
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

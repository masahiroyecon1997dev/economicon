from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from .utilities.create_response import (create_success_response,
                                        create_error_response)
from .utilities.create_log import create_log_api_request
from .utilities.validator.input_request_validators import (
    validate_delete_column_request,
)
from .data.tables_info import all_tables_info


class DeleteColumn(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            # バリデーション
            validation_error = validate_delete_column_request(request_data)
            if validation_error:
                return validation_error

            table_name = request_data['tableName']
            column_name = request_data['columnName']

            df = all_tables_info[table_name].table

            new_df = df.drop(column_name)

            all_tables_info[table_name].table = new_df

            result = {'tableName': table_name}
            return create_success_response(status.HTTP_200_OK, result)

        except Exception as e:
            message = _("An unexpected error occurred "
                        "during renaming table processing")
            return create_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                         message,
                                         e)

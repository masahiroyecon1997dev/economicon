from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from .utilities.create_response import (create_success_response,
                                        create_error_response)
from .utilities.create_log import create_log_api_request
from .utilities.validator.input_request_validators import (
    validate_rename_table_request,
)
from .data.tables_info import all_tables_info


class RenameTableName(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            # バリデーション
            validation_error = validate_rename_table_request(request_data)
            if validation_error:
                return validation_error

            old_table_name = request_data['oldTableName']
            new_table_name = request_data['newTableName']

            table_info = all_tables_info.pop(old_table_name)
            table_info.table_name = new_table_name
            all_tables_info[new_table_name] = table_info

            result = {'tableName': new_table_name}
            return create_success_response(status.HTTP_200_OK, result)

        except Exception as e:
            message = _("An unexpected error occurred "
                        "during renaming table processing")
            return create_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                         message,
                                         e)

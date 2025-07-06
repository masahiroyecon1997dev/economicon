from rest_framework import status
from rest_framework.views import APIView
import polars as pl
import json
from django.utils.translation import gettext as _
from .utilities.create_response import (create_success_response,
                                        create_error_response)
from .utilities.create_log import create_log_api_request
from .utilities.validator.input_request_validators import (
    validate_create_table_request,
)
from .data.tables_info import (TableInfo, all_tables_info)


class CreateTable(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            # バリデーション
            validation_error = validate_create_table_request(request_data)
            if validation_error:
                return validation_error

            table_name = request_data['tableName']
            table_number_of_rows = request_data['tableNumberOfRows']
            new_columns_name = request_data['columns']

            new_column_data_none = [None] * table_number_of_rows

            data = {}
            for column_name in new_columns_name:
                data[column_name] = new_column_data_none

            df = pl.DataFrame(data)
            table_info = TableInfo(
                table_name=table_name,
                table=df
            )
            all_tables_info[table_name] = table_info
            result = {'tableName': table_name}
            return create_success_response(
                status.HTTP_200_OK,
                result,
            )
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding column processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

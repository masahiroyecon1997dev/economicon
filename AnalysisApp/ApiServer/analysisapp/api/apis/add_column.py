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


class AddColumn(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            # バリデーション
            validation_error = validate_add_column_request(request_data)
            if validation_error:
                return validation_error

            table_name = request_data['tableName']
            new_column_name = request_data['newColumnName']
            insert_position_column = request_data['addPositionColumn']

            df = all_tables_info[table_name].table
            num_rows = all_tables_info[table_name].num_rows
            new_column_data_none = [None] * num_rows
            insert_index = df.columns.index(insert_position_column) + 1
            df_with_new_col = df.insert_column(
                index=insert_index,
                column=pl.Series(new_column_name, new_column_data_none))
            # 新しい列をデータフレームに追加
            all_tables_info[table_name].table = df_with_new_col
            result = {'tableName': table_name,
                      'columnName': new_column_name}
            return create_success_response(
                status.HTTP_200_OK,
                result)

        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding column processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

from rest_framework import status
from rest_framework.views import APIView
import json
import polars as pl
from django.utils.translation import gettext as _
from .utilities.create_response import (create_success_response,
                                        create_error_response)
from .utilities.create_log import create_log_api_request
from .utilities.validator.input_request_validators import (
    validate_input_cell_data_request,
)
from .data.tables_info import all_tables_info


class InputCellData(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            # バリデーション
            validation_error = validate_input_cell_data_request(request_data)
            if validation_error:
                return validation_error

            table_name = request_data['tableName']
            column_name = request_data['columnName']
            row_index = request_data['rowIndex']
            new_value = request_data['newValue']

            df = all_tables_info[table_name].table

            numpy_array = df.get_column(column_name).to_list().copy()

            numpy_array[row_index] = new_value

            modified_series = pl.Series(name=column_name,
                                        values=numpy_array,
                                        strict=False)

            new_df = df.with_columns(
                modified_series
            )

            all_tables_info[table_name].table = new_df

            result = {'tableName': table_name}
            return create_success_response(status.HTTP_200_OK, result)

        except Exception as e:
            message = _("An unexpected error occurred "
                        "during renaming table processing")
            return create_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                         message,
                                         e)

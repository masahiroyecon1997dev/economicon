from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import polars as pl
import json
from django.utils.translation import gettext as _
from .utilities.create_response import (create_success_response,
                                        create_error_response)
from .data.tables_info import (TableInfo, all_tables_info)


class AddColumn(APIView):

    def post(self, request):
        try:
            data = tables
            requestData = json.loads(request.body)
            table_name = requestData['tableName']
            new_column_name = requestData['columnName']
            insert_position_column = requestData['insertPositionColumn']
            validation_error = validate_add_column_request(request)
            if validation_error:
                return validation_error

            df = data[table_name]
            num_rows = df.height
            new_column_data_none = [None] * num_rows
            insert_index = df.columns.index(insert_position_column) + 1
            df_with_new_col = df.insert_column(
                index=insert_index,
                column=pl.Series(name=new_column_name),
                values=new_column_data_none)
            # 新しい列をデータフレームに追加
            data[table_name] = df_with_new_col
            result = {'tableName': table_name,
                      'columnName': new_column_name}
            return create_success_response(
                status.HTTP_200_OK,
                result)

        except Exception as e:
            message = _("An unexpected error occurred during EXCEL processing")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                e
            )

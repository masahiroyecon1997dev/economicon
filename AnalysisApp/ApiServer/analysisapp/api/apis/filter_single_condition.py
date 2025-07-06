from rest_framework import status
from rest_framework.views import APIView
import polars as pl
import json
from django.utils.translation import gettext as _
from .utilities.create_response import (create_success_response,
                                        create_error_response)
from .utilities.create_log import create_log_api_request
from .utilities.validator.input_request_validators import (
    validate_filter_single_condition_request,
)
from .data.tables_info import all_tables_info


class FilterSingleCondition(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            # バリデーション
            validation_error = validate_filter_single_condition_request(
                request_data)
            if validation_error:
                return validation_error

            table_name = request_data['tableName']
            column_name = request_data['columnName']
            condition = request_data['condition']
            is_compare_column = request_data['isCompareColumn']
            compare_value = request_data['compareValue']

            df = all_tables_info[table_name].table

            match condition:
                case 'equals':
                    if is_compare_column == 'true':
                        filtered_df = df.filter(
                            pl.col(column_name) == pl.col(compare_value))
                    else:
                        filtered_df = df.filter(
                            pl.col(column_name) == compare_value)
                case 'notEquals':
                    if is_compare_column == 'true':
                        filtered_df = df.filter(
                            pl.col(column_name) != pl.col(compare_value))
                    else:
                        filtered_df = df.filter(
                            pl.col(column_name) != compare_value)
                case 'greaterThan':
                    if is_compare_column == 'true':
                        filtered_df = df.filter(
                            pl.col(column_name) > pl.col(compare_value))
                    else:
                        filtered_df = df.filter(
                            pl.col(column_name) > compare_value)
                case 'greaterThanOrEquals':
                    if is_compare_column == 'true':
                        filtered_df = df.filter(
                            pl.col(column_name) >= pl.col(compare_value))
                    else:
                        filtered_df = df.filter(
                            pl.col(column_name) >= compare_value)
                case 'lessThan':
                    if is_compare_column == 'true':
                        filtered_df = df.filter(
                            pl.col(column_name) < pl.col(compare_value))
                    else:
                        filtered_df = df.filter(
                            pl.col(column_name) < compare_value)
                case 'lessThanOrEquals':
                    if is_compare_column == 'true':
                        filtered_df = df.filter(
                            pl.col(column_name) <= pl.col(compare_value))
                    else:
                        filtered_df = df.filter(
                            pl.col(column_name) <= compare_value)
                case _:
                    # 条件が一致しない場合は元のDataFrameを返す
                    filtered_df = df
            all_tables_info[table_name].table = filtered_df

            result = {'tableName': table_name}
            return create_success_response(status.HTTP_200_OK, result)

        except Exception as e:
            message = _("An unexpected error occurred "
                        "during renaming table processing")
            return create_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                         message,
                                         e)

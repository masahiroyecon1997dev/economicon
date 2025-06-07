from rest_framework import status
from rest_framework.views import APIView
from django.utils.translation import gettext as _
import io
import polars as pl
from .utilities.create_response import create_success_response
from .utilities.create_response import create_error_response
from .utilities.create_log import create_log_api_request
from .utilities.validator.file_request_validators import (
    validate_parquet_request)
from .utilities.create_table_name import create_table_name_by_file_name
from .data.tables import tables


class ImportParquetByFile(APIView):
    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # バリデーション
            validation_error = validate_parquet_request(request)
            if validation_error:
                return validation_error

            # polarsデータフレーム化
            uploaded_file = request.FILES['file']
            table_name = create_table_name_by_file_name(uploaded_file.name,
                                                        tables)
            tables[table_name] = pl.read_parquet(
                io.BytesIO(uploaded_file.read()))
            result = {'tableName': table_name}
            return create_success_response(
                status.HTTP_200_OK,
                result,
            )
        except pl.NoDataError as e:
            message = _("The uploaded PARQUET file is "
                        "empty or contains no valid data.")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                e
            )
        except pl.ComputeError as e:
            message = _("Failed to parse PARQUET file: "
                        "Invalid format or encoding.")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                e
            )
        except Exception as e:
            message = _("An unexpected error occurred during PARQUET "
                        "processing")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                e
            )

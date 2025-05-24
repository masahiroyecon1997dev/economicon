from rest_framework import status
from rest_framework.views import APIView
from django.utils.translation import gettext as _
import io
import polars as pl
from .utilities.create_response import create_success_response
from .utilities.create_response import create_error_response
from .utilities.create_log import create_log_api_request
from .data.tables import tables


class ImportTsvByFile(APIView):

    def post(self, request):
        try:
            create_log_api_request(request)
            data = tables
            if 'file' not in request.data:
                message = _("No file uploaded.")
                return create_error_response(
                    status.HTTP_400_BAD_REQUEST,
                    message,
                    request
                )
            uploaded_file = request.FILES["file"]
            # タブ区切りチェック
            if not uploaded_file.name.lower().endswith(('.tsv', '.txt')):
                message = _("Uploaded file is not a TSV file.")
                return create_error_response(
                    status.HTTP_400_BAD_REQUEST,
                    message,
                    request
                )
            file_name: str = uploaded_file.name
            table_name: str = file_name.split('.')[0]
            data[table_name] = pl.read_csv(io.BytesIO(uploaded_file.read()),
                                           separator='\t')
            result = {'tableName': table_name}
            return create_success_response(
                status.HTTP_200_OK,
                result,
                request
            )
        except pl.NoDataError as e:
            message = _("The uploaded TSV file is "
                        "empty or contains no valid data.")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                request,
                e
            )
        except pl.PanicException as e:
            message = _("Failed to parse TSV file.")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                request,
                e
            )
        except Exception as e:
            message = _("An unexpected error occurred during TSV processing")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                request,
                e
            )

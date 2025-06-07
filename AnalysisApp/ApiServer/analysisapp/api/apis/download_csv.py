from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from io import StringIO
from .data.tables import tables
from django.utils.translation import gettext as _
from .utilities.create_response import create_error_response


class DownloadDataFrameAsCsvView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            table_name: str = request.query_params.get('tableName')
            data = tables[table_name]

            csv_buffer = StringIO()
            data.write_csv(csv_buffer)
            csv_content = csv_buffer.getvalue()

            response = Response(csv_content, content_type='text/csv')
            # ダウンロードファイル名を設定
            response['Content-Disposition'] = 'attachment; '
            f'filename="${table_name}.csv"'

            return response
        except Exception as e:
            # エラーハンドリング
            message = _("Failed to generate or download CSV")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

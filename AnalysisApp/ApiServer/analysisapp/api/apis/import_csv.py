from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import io
import polars as pl

from .tables import tables


class ImportCsv(APIView):
    def post(self, request):
        try:
            data = tables
            csv_file = request.FILES["file"]
            decoded_file = csv_file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            file_name: str = csv_file.name
            table_name: str = file_name.split('.')[0]
            data[table_name] = pl.read_csv(io_string, encoding='utf8')
            result = {'code': 0, 'result': {'tableName': table_name},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

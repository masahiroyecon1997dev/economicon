from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import polars as pl

from .tables import tables


class ReadCsv(APIView):
    def post(self, request):
        try:
            data = tables
            path: str = request.query_params.get('path')
            table_name = path.split('/')[-1][:-4]
            data[table_name] = pl.read_csv(path, encoding='utf8')
            result = {'code': 0, 'result': {'tableName': table_name},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

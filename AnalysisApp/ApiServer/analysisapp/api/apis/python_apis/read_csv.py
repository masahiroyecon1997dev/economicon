from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import polars as pl

from .data.tables_info import (TableInfo, all_tables_info)


class ReadCsv(APIView):
    def post(self, request):
        try:
            path: str = request.query_params.get('path')
            table_name = path.split('/')[-1][:-4]
            df = pl.read_csv(path, encoding='utf8')
            table_info = TableInfo(
                table_name=table_name,
                table=df
            )
            all_tables_info[table_name] = table_info
            result = {'code': 0, 'result': {'tableName': table_name},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

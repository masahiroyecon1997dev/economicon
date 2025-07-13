from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .data.tables_info import all_tables_info


class GetColumnNameList(APIView):
    def get(self, request):
        try:
            table_name: str = request.query_params.get('tableName')
            data = all_tables_info[table_name].table
            column_names = data[table_name].columns
            columns = []
            for i, name in enumerate(column_names):
                dictionary = {'id': i + 1, 'name': name}
                columns.append(dictionary)
            result = {'code': 0, 'result': {'columnList': columns},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'columnList': []},
                      'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

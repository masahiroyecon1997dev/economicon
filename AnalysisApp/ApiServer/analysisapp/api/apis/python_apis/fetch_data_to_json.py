from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .data.tables_info import all_tables_info


class FetchDataToJson(APIView):
    def get(self, request):
        try:
            table_name: str = request.query_params.get('tableName')
            first_row: int = int(request.query_params.get('firstRow'))
            last_row: int = int(request.query_params.get('lastRow'))
            data = all_tables_info[table_name].table
            data_to_json = (data[first_row - 1:last_row]
                            .write_json())
            result = {'code': 0, 'result': {'tableName': table_name,
                                            'data': data_to_json},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': '', 'data': ''},
                      'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

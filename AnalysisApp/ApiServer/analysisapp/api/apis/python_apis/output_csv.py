from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .data.tables_info import all_tables_info


class OutputCsv(APIView):
    def get(self, request):
        try:
            table_name: str = request.query_params.get('tableName')
            data = all_tables_info[table_name].table
            csv_table_data: str = data.write_csv()
            print(csv_table_data)
            result = {'code': 0, 'result': {'csvData': csv_table_data},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'csvData': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .tables import tables


class OutputCsv(APIView):
    def get(self, request):
        try:
            data = tables
            table_name: str = request.query_params.get('tableName')
            csv_table_data: str = data[table_name].write_csv()
            print(csv_table_data)
            result = {'code': 0, 'result': {'csvData': csv_table_data},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'csvData': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

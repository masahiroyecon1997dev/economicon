from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .tables import tables


class WriteCsv(APIView):
    def get(self, request):
        try:
            data = tables
            path: str = request.query_params.get('path')
            file_name: str = request.query_params.get('fileName')
            table_name: str = request.query_params.get('tableName')
            savePath: str = path + '/' + file_name
            data[table_name].write_csv(savePath)
            result = {'code': 0, 'result': {'savePath': ''}, 'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'savePath': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

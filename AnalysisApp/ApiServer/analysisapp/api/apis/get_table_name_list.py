from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .data.tables import tables


class GetTableNameList(APIView):
    def get(self, request):
        try:
            data = tables
            table_names = data.keys()
            result = {'code': 0, 'result': {'tableNameList': table_names},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableNameList': []},
                      'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

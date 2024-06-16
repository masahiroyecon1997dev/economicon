from django.shortcuts import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

import polars as pl

data = pl.DataFrame()


def index(request):
    return HttpResponse("Hello, world")


class ReadCsv(APIView):
    def get(self, request):
        global data
        path = request.query_params.get('path')
        data = pl.read_csv(path, encoding='utf8')
        return Response('success', status=status.HTTP_200_OK)


class WriteCsv(APIView):
    def get(self, request):
        global data
        path = request.query_params.get('path')
        file_name = request.query_params.get('fileName')
        data.write_csv(path + '/' + file_name)
        return Response(path + '/' + file_name, status=status.HTTP_200_OK)

import io
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


class ImportCsv(APIView):
    def post(self, request):
        global data
        csv_file = request.FILES["file"]
        decoded_file = csv_file.read().decode("utf-8")
        io_string = io.StringIO(decoded_file)
        print(request.FILES["file"])
        data = pl.read_csv(io_string, encoding='utf8')
        return Response('success', status=status.HTTP_200_OK)

import io
import json
import random
from django.shortcuts import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

import polars as pl

data = {}


def index(request):
    return HttpResponse("Hello, world")


class ReadCsv(APIView):
    def get(self, request):
        try:
            global data
            path: str = request.query_params.get('path')
            table_name = path.split('/')[-1][:-4]
            data[table_name] = pl.read_csv(path, encoding='utf8')
            result = {'code': 0, 'tableName': table_name}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class WriteCsv(APIView):
    def get(self, request):
        try:
            global data
            path: str = request.query_params.get('path')
            file_name: str = request.query_params.get('fileName')
            table_name: str = request.query_params.get('tableName')
            savePath: str = path + '/' + file_name
            data[table_name].write_csv(savePath)
            result = {'code': 0, 'savePath': savePath}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class ImportCsv(APIView):
    def post(self, request):
        try:
            global data
            csv_file = request.FILES["file"]
            decoded_file = csv_file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            file_name: str = csv_file.name
            table_name: str = file_name.split('.')[0]
            data[table_name] = pl.read_csv(io_string, encoding='utf8')
            result = {'code': 0, 'tableName': table_name}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class OutputCsv(APIView):
    def get(self, request):
        try:
            global data
            table_name: str = request.query_params.get('tableName')
            csv_table_data: str = data[table_name].write_csv()
            print(csv_table_data)
            result = {'code': 0, 'csvData': csv_table_data}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class FetchDataToJson(APIView):
    def get(self, request):
        try:
            global data
            table_name: str = request.query_params.get('tableName')
            print(table_name)
            print(data)
            data_to_json = data[table_name].write_json()
            result = {'code': 0, 'tableName': table_name, 'data': data_to_json}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class GetTableNameList(APIView):
    def get(self, request):
        try:
            global data
            table_names = data.keys()
            result = {'code': 0, 'tableNameList': table_names}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class GetColumnNameList(APIView):
    def get(self, request):
        try:
            global data
            table_name: str = request.query_params.get('tableName')
            column_names = data[table_name].columns
            result = {'code': 0, 'columnNameList': column_names}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class GenerateSimulationData(APIView):
    def post(self, request):
        try:
            global data
            requestData = json.loads(request.body)

            table_name = requestData['tableName']
            df = pl.DataFrame()

            for params in requestData['dataStructure']:
                column_name = params['columnName']
                min_value = params['minValue']
                max_value = params['maxValue']
                num_samples = params['numSamples']

                series = ([random.uniform(min_value, max_value)
                           for _ in range(num_samples)]).alias(column_name)
                df.with_columns(series)

            data[table_name] = df

        except Exception as e:
            result = {'code': -9999, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

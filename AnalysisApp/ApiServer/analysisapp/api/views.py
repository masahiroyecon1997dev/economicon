import io
import json
import numpy as np
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
            result = {'code': 0, 'result': {'tableName': table_name},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
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
            result = {'code': 0, 'result': {'savePath': ''}, 'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'savePath': ''}, 'message': e}
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
            result = {'code': 0, 'result': {'tableName': table_name},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class OutputCsv(APIView):
    def get(self, request):
        try:
            global data
            table_name: str = request.query_params.get('tableName')
            csv_table_data: str = data[table_name].write_csv()
            print(csv_table_data)
            result = {'code': 0, 'result': {'csvData': csv_table_data},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'csvData': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class FetchDataToJson(APIView):
    def get(self, request):
        try:
            global data
            table_name: str = request.query_params.get('tableName')
            first_row: int = int(request.query_params.get('firstRow'))
            last_row: int = int(request.query_params.get('lastRow'))
            data_to_json = (data[table_name][first_row - 1:last_row]
                            .write_json())
            result = {'code': 0, 'result': {'tableName': table_name,
                                            'data': data_to_json},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': '', 'data': ''},
                      'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class GetTableNameList(APIView):
    def get(self, request):
        try:
            global data
            table_names = data.keys()
            result = {'code': 0, 'result': {'tableNameList': table_names},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableNameList': []},
                      'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class GetColumnNameList(APIView):
    def get(self, request):
        try:
            global data
            table_name: str = request.query_params.get('tableName')
            column_names = data[table_name].columns
            result = {'code': 0, 'result': {'columnNameList': column_names},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'columnNameList': []},
                      'message': e}
            return Response(data=result, status=status.HTTP_200_OK)


class GenerateSimulationData(APIView):
    def post(self, request):
        try:
            global data
            requestData = json.loads(request.body)
            table_name = requestData['tableName']
            num_samples = requestData['numSamples']
            error_mean = requestData['errorMean']
            error_variance = requestData['errorVariance']
            df = pl.DataFrame({'result': np.full(num_samples, 0).tolist()})
            for params in requestData['dataStructure']:
                column_name = params['columnName']
                coefficient = params['coefficient']
                min_value = params['minValue']
                max_value = params['maxValue']
                sample_data_series = pl.Series(name=column_name,
                                               values=np.random.uniform(
                                                   low=min_value,
                                                   high=max_value,
                                                   size=num_samples))
                df = df.with_columns(sample_data_series.alias(column_name))
                coef_column_name = column_name + '_coef'
                df = df.with_columns(pl.lit(coefficient)
                                     .alias(coef_column_name))
                df = df.with_columns((pl.col('result') +
                                      pl.col(column_name)*pl.col(
                                          coef_column_name)).alias('result'))
                df = df.drop([coef_column_name])
            error_series = pl.Series(name='error',
                                     values=np.random.normal(
                                               loc=error_mean,
                                               scale=error_variance**0.5,
                                               size=num_samples))
            df = df.with_columns(error_series.alias('error'))
            df = df.with_columns((pl.col('result') + pl.col('error'))
                                 .alias('result'))
            df = df.drop(['error'])
            data[table_name] = df
            result = {'code': 0, 'result': {'tableName': table_name},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

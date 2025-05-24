from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import numpy as np
import polars as pl
import json

from .data.tables import tables


class AddColumnWithSimulationData(APIView):
    def post(self, request):
        try:
            data = tables
            requestData = json.loads(request.body)
            table_name = requestData['tableName']
            df = data[table_name]
            num_rows = df.shape[0]
            column_name = requestData['columnName']
            data_type = requestData['dataType']
            match data_type:
                case 'constant':
                    constant = requestData['value1']
                    sample_data_series = pl.Series(
                        name=column_name,
                        values=np.full(num_rows, constant).tolist())
                case 'uniform':
                    min_value = requestData['value1']
                    max_value = requestData['value2']
                    sample_data_series = pl.Series(
                        name=column_name,
                        values=np.random.uniform(
                            low=min_value,
                            high=max_value,
                            size=num_rows))
                case 'normal':
                    mean = requestData['value1']
                    variance = requestData['value2']
                    sample_data_series = pl.Series(
                        name=column_name,
                        values=np.random.normal(
                            loc=mean,
                            scale=variance**0.5,
                            size=num_rows))
                case '_':
                    sample_data_series = pl.Series(
                        name=column_name,
                        values=np.full(num_rows, 0).tolist())
            df = df.with_columns(sample_data_series.alias(column_name))
            data[table_name] = df
            result = {'code': 0, 'result': {'tableName': table_name},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

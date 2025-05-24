from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import numpy as np
import polars as pl
import json

from .data.tables import tables


class GenerateSimulationData(APIView):
    def post(self, request):
        try:
            data = tables
            requestData = json.loads(request.body)
            table_name = requestData['tableName']
            num_samples = requestData['numSamples']
            df = pl.DataFrame()
            for params in requestData['dataStructure']:
                column_name = params['columnName']
                data_type = params['dataType']
                match data_type:
                    case 'constant':
                        constant = params['value1']
                        sample_data_series = pl.Series(
                            name=column_name,
                            values=np.full(num_samples, constant).tolist())
                    case 'uniform':
                        min_value = params['value1']
                        max_value = params['value2']
                        sample_data_series = pl.Series(
                            name=column_name,
                            values=np.random.uniform(
                                low=min_value,
                                high=max_value,
                                size=num_samples))
                    case 'normal':
                        mean = params['value1']
                        variance = params['value2']
                        sample_data_series = pl.Series(
                            name=column_name,
                            values=np.random.normal(
                                loc=mean,
                                scale=variance**0.5,
                                size=num_samples))
                    case '_':
                        sample_data_series = pl.Series(
                            name=column_name,
                            values=np.full(num_samples, 0).tolist())
                df = df.with_columns(sample_data_series.alias(column_name))
            data[table_name] = df
            result = {'code': 0, 'result': {'tableName': table_name},
                      'message': ''}
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

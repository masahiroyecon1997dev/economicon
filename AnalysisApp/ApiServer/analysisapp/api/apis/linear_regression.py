import statsmodels.api as sm
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .tables import tables


class LinearRegression(APIView):
    def post(self, request):
        try:
            table_name: str = request.query_params.get('tableName')
            data = tables[table_name]
            print(data)
            X = data[['X1', 'X2']]
            Y = data['Y']
            X = sm.add_constant(X)
            model = sm.OLS(Y, X).fit()
            print(model.summary())
            return Response(data=model, status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

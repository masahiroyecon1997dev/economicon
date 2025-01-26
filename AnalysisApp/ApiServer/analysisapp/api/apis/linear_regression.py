import statsmodels.api as sm
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import json

from .tables import tables


class LinearRegression(APIView):
    def post(self, request):
        try:
            requestData = json.loads(request.body)
            table_name = requestData['tableName']
            dependent_variable = requestData['dependentVariable']
            explanatory_variable = requestData['explanatoryVariables']
            data = tables[table_name]
            Y = data[dependent_variable].to_numpy()
            X = data.select(explanatory_variable).to_numpy()
            X = sm.add_constant(X)
            model = sm.OLS(Y, X).fit()
            summary = model.summary().as_text()
            result = {'code': 0,
                      'result': {
                          'regressionResult': summary},
                      'message': ''}
            return Response(data=result,
                            status=status.HTTP_200_OK)
        except Exception as e:
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

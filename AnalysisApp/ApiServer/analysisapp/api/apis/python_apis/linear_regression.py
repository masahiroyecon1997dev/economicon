import statsmodels.api as sm
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import json

from .data.tables_info import all_tables_info


class LinearRegression(APIView):
    def post(self, request):
        try:
            requestData = json.loads(request.body)
            table_name = requestData['tableName']
            dependent_variable = requestData['dependentVariable']
            explanatory_variable = requestData['explanatoryVariables']
            data = all_tables_info[table_name].table
            Y = data[dependent_variable].to_numpy()
            X = data.select(explanatory_variable).to_numpy()
            X = sm.add_constant(X)
            model = sm.OLS(Y, X).fit()
            print(model)
            print(model.params)
            summary = {
                # 'variables': model.params.index.tolist(),
                # 'params': model.params.values.tolist(),
                # 'pValues': model.pvalues.values.tolist(),
                # 'tValues': model.tvalues.values.tolist(),
                'AIC': model.aic,
                'BIC': model.bic,
                'R2': model.rsquared,
                'AdjR2': model.rsquared_adj
            }
            print(summary)
            summary = model.summary().as_text()
            result = {'code': 0,
                      'result': {
                          'regressionResult': summary},
                      'message': ''}
            return Response(data=result,
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            result = {'code': -9999, 'result': {'tableName': ''}, 'message': e}
            return Response(data=result, status=status.HTTP_200_OK)

from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..python_apis.variable_effects_estimation import variable_effects_estimation
from ..python_apis.common_api_class import ApiError


class VariableEffectsEstimation(APIView):
    """
    変量効果推定分析を行うREST APIクラス

    POST /api/variable-effects-estimation
    {
        "tableName": "テーブル名",
        "dependentVariable": "被説明変数の列名",
        "explanatoryVariables": ["説明変数1", "説明変数2", ...],
        "standardErrorMethod": "nonrobust|HC0|HC1|HC2|HC3|HAC|cluster",
        "useTDistribution": true|false
    }
    """

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)

            # リクエストデータの取得
            request_data = json.loads(request.body)
            table_name = request_data['tableName']
            dependent_variable = request_data['dependentVariable']
            explanatory_variables = request_data['explanatoryVariables']
            
            # オプションパラメータ（デフォルト値を設定）
            standard_error_method = request_data.get('standardErrorMethod', 'nonrobust')
            use_t_distribution = request_data.get('useTDistribution', True)

            # 変量効果推定分析の実行
            result = variable_effects_estimation(
                table_name=table_name,
                dependent_variable=dependent_variable,
                explanatory_variables=explanatory_variables,
                standard_error_method=standard_error_method,
                use_t_distribution=use_t_distribution
            )

            return create_success_response(
                status.HTTP_200_OK,
                result)

        except ValidationError as e:
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                e.message
            )
        except ApiError as e:
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                e.message
            )
        except KeyError as e:
            message = _("Required parameter is missing: {}").format(str(e))
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message
            )
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "variable effects estimation processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )
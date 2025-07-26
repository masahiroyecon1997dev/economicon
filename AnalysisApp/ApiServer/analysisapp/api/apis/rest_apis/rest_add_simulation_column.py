from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..python_apis.add_simulation_column import add_simulation_column
from ..python_apis.common_api_class import ApiError


class AddSimulationColumn(APIView):
    """
    シミュレーションデータの列を追加するREST API
    
    POSTリクエストで以下のパラメータを受け取ります：
    - tableName: 対象テーブル名
    - newColumnName: 追加する列名
    - distributionType: 分布の種類
    - distributionParams: 分布のパラメータ（分布ごとに異なる）
    """

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            
            # リクエストデータの取得
            request_data = json.loads(request.body)
            table_name = request_data['tableName']
            new_column_name = request_data['newColumnName']
            distribution_type = request_data['distributionType']
            distribution_params = request_data['distributionParams']
            
            result = add_simulation_column(
                table_name=table_name,
                new_column_name=new_column_name,
                distribution_type=distribution_type,
                distribution_params=distribution_params
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
            message = _("Missing required parameter: {key}").format(key=str(e))
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message
            )
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding simulation column processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )
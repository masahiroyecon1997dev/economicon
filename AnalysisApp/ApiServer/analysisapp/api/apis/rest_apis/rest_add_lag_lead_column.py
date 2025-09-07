from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..python_apis.add_lag_lead_column import add_lag_lead_column
from ..python_apis.common_api_class import ApiError


class AddLagLeadColumn(APIView):

    def post(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # リクエストデータの取得
            request_data = json.loads(request.body)
            table_name = request_data.get('tableName')
            source_column = request_data.get('sourceColumn')
            new_column_name = request_data.get('newColumnName')
            periods = request_data.get('periods')
            group_columns = request_data.get('groupColumns', [])

            result = add_lag_lead_column(
                table_name=table_name,
                source_column=source_column,
                new_column_name=new_column_name,
                periods=periods,
                group_columns=group_columns
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
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding lag/lead column processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

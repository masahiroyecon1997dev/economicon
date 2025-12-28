from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.views import APIView

from ..python_apis.abstract_api import ApiError
from ..python_apis.get_settings import get_setting
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (create_error_response,
                                         create_success_response)
from ..utilities.validator.common_validators import ValidationError


class GetSettings(APIView):
    """
    アプリケーション設定を取得するREST APIクラス

    GET リクエストでアプリケーションの設定情報を返します。
    """

    def get(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)

            # 設定を取得
            result = get_setting()

            return create_success_response(
                status.HTTP_200_OK,
                result
            )

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
                        "getting settings processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

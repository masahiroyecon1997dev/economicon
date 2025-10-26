from rest_framework import status
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..python_apis.get_list_files import get_list_files
from ..python_apis.common_api_class import ApiError


class GetListFiles(APIView):

    def get(self, request):
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)
            # クエリパラメータの取得
            directory_path = request.query_params.get('directoryPath')
            result = get_list_files(directory_path=directory_path)
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
                        "listing files processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

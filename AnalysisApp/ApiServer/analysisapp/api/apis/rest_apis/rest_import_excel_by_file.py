from rest_framework.views import APIView
from rest_framework import status
from django.utils.translation import gettext as _
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (
    create_success_response,
    create_error_response
)
from ..utilities.validator.file_request_validators \
    import validate_excel_request
from ..python_apis.import_excel_by_file import (
    import_excel_by_file,
    ApiError
)


class RestImportExcelByFile(APIView):
    """
    EXCELファイルインポートAPIのRESTエンドポイント
    """
    def post(self, request):
        try:
            create_log_api_request(request)
            # バリデーション
            validation_error = validate_excel_request(request)
            if validation_error:
                return validation_error
            uploaded_file = request.FILES['file']
            file_name = uploaded_file.name
            file_bytes = uploaded_file.read()
            result = import_excel_by_file(file_name, file_bytes)
            return create_success_response(status.HTTP_200_OK, result)
        except ApiError as e:
            return create_error_response(status.HTTP_400_BAD_REQUEST, str(e))
        except Exception as e:
            message = _(
                "An unexpected error occurred during EXCEL processing"
            )
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message,
                e
            )

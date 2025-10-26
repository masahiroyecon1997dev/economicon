from rest_framework import status
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_log import create_log_api_request
from ..utilities.validator.file_request_validators import validate_csv_request
from ..python_apis.import_csv_by_file import import_csv_by_file
from ..python_apis.common_api_class import ApiError


class ImportCsvByFile(APIView):
    """
    CSVファイルインポート用のREST APIクラス

    アップロードされたCSVファイルを処理し、新しいテーブルを作成します。
    """

    def post(self, request):
        """
        CSVファイルをアップロードしてテーブルを作成する

        Args:
            request: HTTPリクエストオブジェクト

        Returns:
            レスポンスオブジェクト
        """
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)

            # バリデーション
            validation_error = validate_csv_request(request)
            if validation_error:
                return validation_error

            # ファイルデータを取得
            uploaded_file = request.FILES['file']

            # Python APIを呼び出し
            result = import_csv_by_file(
                file_data=uploaded_file,
                file_name=uploaded_file.name
            )

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
                        "CSV import processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

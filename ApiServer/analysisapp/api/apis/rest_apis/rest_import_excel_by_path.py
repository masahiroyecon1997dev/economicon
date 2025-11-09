from rest_framework.views import APIView
from rest_framework import status
import json
from django.utils.translation import gettext as _
from ..utilities.create_log import create_log_api_request
from ..utilities.create_response import (
    create_success_response,
    create_error_response
)
from ..utilities.validator.common_validators import ValidationError
from ..python_apis.import_excel_by_path import import_excel_by_path
from ..python_apis.common_api_class import ApiError


class RestImportExcelByPath(APIView):
    """
    Excelファイルインポート用のREST APIクラス

    指定されたパスのExcelファイルを処理し、指定されたテーブル名でテーブルを作成します。
    """

    def post(self, request):
        """
        EXCELファイルをパス指定でインポートしてテーブルを作成する

        Args:
            request: HTTPリクエストオブジェクト
                     JSON body: {
                         "filePath": "EXCELファイルのパス",
                         "tableName": "作成するテーブル名",
                         "sheetName": "シート名（オプション）"
                     }

        Returns:
            レスポンスオブジェクト
        """
        try:
            # リクエスト受け取りログ
            create_log_api_request(request)

            # JSONデータの取得
            request_data = json.loads(request.body)

            # パラメータの取得
            file_path = request_data.get('filePath')
            table_name = request_data.get('tableName')
            sheet_name = request_data.get('sheetName')

            # Python APIを呼び出し
            result = import_excel_by_path(
                file_path=file_path,
                table_name=table_name,
                sheet_name=sheet_name
            )

            return create_success_response(
                status.HTTP_200_OK,
                result
            )

        except json.JSONDecodeError:
            message = _("Invalid JSON format in request body")
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                message
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
                        "EXCEL import processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

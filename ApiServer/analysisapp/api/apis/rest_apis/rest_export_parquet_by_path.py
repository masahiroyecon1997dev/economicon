from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _
from ..utilities.create_response import (create_success_response,
                                         create_error_response)
from ..utilities.create_log import create_log_api_request
from ..python_apis.export_parquet_by_path import export_parquet_by_path
from ..python_apis.abstract_api import ApiError
from ..utilities.validator.common_validators import ValidationError


class ExportParquetByPath(APIView):
    """
    PARQUETファイルパス指定エクスポート用のREST APIクラス

    指定されたテーブル名のデータを指定されたパスにPARQUETファイルとして出力します。
    """

    def post(self, request):
        """
        テーブルをPARQUETファイルにパス指定でエクスポートする

        Args:
            request: HTTPリクエストオブジェクト
                     JSON body: {
                         "tableName": "エクスポートするテーブル名",
                         "directoryPath": "出力するディレクトリパス",
                         "fileName": "出力するPARQUETファイル名"
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
            table_name = request_data.get('tableName')
            directory_path = request_data.get('directoryPath')
            file_name = request_data.get('fileName')

            # Python APIを呼び出し
            result = export_parquet_by_path(
                table_name=table_name,
                directory_path=directory_path,
                file_name=file_name
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
                        "PARQUET export processing")
            return create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                message,
                e
            )

import os

from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...models import ExportCsvByPathRequestBody
from ...utils import ProcessingError
from ...utils.validators import (
    validate_directory_path,
    validate_existence,
)
from ..data.tables_store import TablesStore


class ExportCsvByPath:
    """
    テーブルをCSVファイルパス指定でエクスポートするAPIクラス

    指定されたテーブル名のデータを指定されたパスにCSVファイルとして出力します。
    区切り文字を指定できます。
    """

    def __init__(self, body: ExportCsvByPathRequestBody):
        # テーブルマネージャーの初期化
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = body.table_name
        # ディレクトリパス
        self.directory_path = body.directory_path
        # ファイル名
        self.file_name = body.file_name
        # 区切り文字
        self.separator = body.separator
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "tableName",
            "directory_path": "directoryPath",
            "file_name": "fileName",
            "separator": "separator",
        }

    def validate(self):
        # 対象のテーブルが存在することを検証
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )

        # ディレクトリパスのバリデーション
        validate_directory_path(
            path_str=self.directory_path,
            target=self.param_names["directory_path"],
        )
        return None

    def execute(self):
        # CSVファイルのエクスポート処理
        try:
            # テーブルを取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            file_path = os.path.join(self.directory_path, self.file_name)

            # CSVファイルに書き込み
            df.write_csv(file_path, separator=self.separator)

            # 結果を返す
            result = {"filePath": file_path}
            return result

        except KeyError as e:
            message = _("Table does not exist: {}").format(self.table_name)
            raise ProcessingError(
                error_code=ErrorCode.TABLE_NOT_FOUND, message=message
            ) from e
        except PermissionError as e:
            message = _(
                "Permission denied: Cannot write to the specified path."
            )
            raise ProcessingError(
                error_code=ErrorCode.PERMISSION_DENIED, message=message
            ) from e
        except Exception as e:
            message = _(
                "An unexpected error occurred during CSV export processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.CSV_EXPORT_ERROR,
                message=message,
                detail=str(e),
            ) from e

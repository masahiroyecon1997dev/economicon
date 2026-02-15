import os

from ...exceptions import ApiError
from ...i18n.translation import gettext as _
from ...models import ExportExcelByPathRequestBody
from ...utils.validators.common import ValidationError
from ...utils.validators.files import (
    validate_directory_path,
    validate_file_name,
)
from ...utils.validators.tables_store import (
    validate_existed_table_name,
)
from ..data.tables_store import TablesStore


class ExportExcelByPath:
    """
    テーブルをEXCELファイルパス指定でエクスポートするAPIクラス

    指定されたテーブル名のデータを指定されたパスにEXCELファイルとして出力します。
    """

    def __init__(self, body: ExportExcelByPathRequestBody):
        # テーブルマネージャーの初期化
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = body.table_name
        # ディレクトリパス
        self.directory_path = body.directory_path
        # ファイル名
        self.file_name = body.file_name
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "tableName",
            "directory_path": "directoryPath",
            "file_name": "fileName",
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            # テーブル名のバリデーション
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )

            # ディレクトリパスのバリデーション
            validate_directory_path(
                self.directory_path, self.param_names["directory_path"]
            )

            # ファイル名のバリデーション
            validate_file_name(self.file_name, self.param_names["file_name"])

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # EXCELファイルのエクスポート処理
        try:
            # テーブルを取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            file_path = os.path.join(self.directory_path, self.file_name)

            # EXCELファイルに書き込み
            df.write_excel(file_path)

            # 結果を返す
            result = {"filePath": file_path}
            return result

        except KeyError as e:
            message = _("Table does not exist: {}").format(self.table_name)
            raise ApiError(message) from e
        except PermissionError as e:
            message = _(
                "Permission denied: Cannot write to the specified path."
            )
            raise ApiError(message) from e
        except Exception as e:
            message = _(
                "An unexpected error occurred during EXCEL export processing"
            )
            raise ApiError(message) from e

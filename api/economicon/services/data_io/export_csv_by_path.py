import os
from typing import Dict

from ...utils.validators.common import ValidationError
from ...utils.validators.file import (
    validate_directory_path,
    validate_file_name,
    validate_separator,
)
from ...utils.validators.tables_store import (
    validate_existed_table_name,
)
from ..abstract_api import AbstractApi, ApiError
from ..data.tables_store import TablesStore
from ...i18n.translation import gettext as _


class ExportCsvByPath(AbstractApi):
    """
    テーブルをCSVファイルパス指定でエクスポートするAPIクラス

    指定されたテーブル名のデータを指定されたパスにCSVファイルとして出力します。
    区切り文字を指定できます。
    """

    def __init__(
        self,
        table_name: str,
        directory_path: str,
        file_name: str,
        separator: str = ",",
    ):
        # テーブルマネージャーの初期化
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = table_name
        # ディレクトリパス
        self.directory_path = directory_path
        # ファイル名
        self.file_name = file_name
        # 区切り文字
        self.separator = separator
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "tableName",
            "directory_path": "directoryPath",
            "file_name": "fileName",
            "separator": "separator",
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

            # 区切り文字のバリデーション
            validate_separator(self.separator, self.param_names["separator"])
            return None
        except ValidationError as e:
            return e

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
            raise ApiError(message) from e
        except PermissionError as e:
            message = _(
                "Permission denied: Cannot write to the specified path."
            )
            raise ApiError(message) from e
        except Exception as e:
            message = _(
                "An unexpected error occurred during CSV export processing"
            )
            raise ApiError(message) from e

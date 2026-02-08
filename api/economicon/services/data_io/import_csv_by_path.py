import polars as pl

from ...exceptions import ApiError
from ...i18n.translation import gettext as _
from ...utils.validators.common import ValidationError
from ...utils.validators.file import (
    validate_file_path,
    validate_separator,
)
from ...utils.validators.tables_store import validate_new_table_name
from ..data.tables_store import TablesStore


class ImportCsvByPath:
    """
    CSVファイルパス指定でデータをインポートしてテーブルを作成するAPIクラス

    指定されたパスのCSVファイルを解析し、指定されたテーブル名で登録します。
    区切り文字を指定できます。
    """

    def __init__(self, file_path: str, table_name: str, separator: str = ","):
        # テーブルマネージャーの初期化
        self.tables_store = TablesStore()
        # ファイルパス
        self.file_path = file_path
        # テーブル名
        self.table_name = table_name
        # 区切り文字
        self.separator = separator
        # パラメータ名のマッピング
        self.param_names = {
            "file_path": "filePath",
            "table_name": "tableName",
            "separator": "separator",
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            # ファイルパスのバリデーション
            validate_file_path(self.file_path, self.param_names["file_path"])
            table_name_list = self.tables_store.get_table_name_list()
            # テーブル名のバリデーション
            validate_new_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            # 区切り文字のバリデーション
            validate_separator(self.separator, self.param_names["separator"])
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # CSVファイルのインポート処理
        try:
            # CSVファイルをPolarsデータフレームに変換
            df = pl.read_csv(
                self.file_path, separator=self.separator, encoding="utf8"
            )

            # テーブルを作成
            created_table_name = self.tables_store.store_table(
                self.table_name, df
            )

            # 結果を返す
            result = {"tableName": created_table_name}
            return result

        except pl.exceptions.NoDataError as e:
            message = _("The CSV file is empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.exceptions.ComputeError as e:
            message = _(
                "Failed to parse CSV file: Invalid format or encoding."
            )
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during CSV processing")
            raise ApiError(message) from e

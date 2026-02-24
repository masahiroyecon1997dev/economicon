import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import ImportFileRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_file_path,
    validate_non_existence,
)


class ImportCsv:
    """
    CSVファイルパス指定でデータをインポートしてテーブルを作成するAPIクラス

    指定されたパスのCSVファイルを解析し、指定されたテーブル名で登録します。
    区切り文字とエンコーディングを指定できます。
    """

    def __init__(
        self,
        body: ImportFileRequestBody,
        tables_store: TablesStore,
    ):
        # テーブルマネージャーの初期化
        self.tables_store = tables_store
        # ファイルパス
        self.file_path = body.file_path
        # テーブル名
        self.table_name = body.table_name
        # 区切り文字
        self.separator = body.separator
        # エンコーディング
        self.encoding = (
            "cp932" if body.encoding == "shift_jis" else body.encoding
        )
        # パラメータ名のマッピング
        self.param_names = {
            "file_path": "filePath",
            "table_name": "tableName",
            "separator": "separator",
            "encoding": "encoding",
        }

    def validate(self):
        # ファイルパスのバリデーション
        validate_file_path(
            path_str=self.file_path, target=self.param_names["file_path"]
        )
        table_name_list = self.tables_store.get_table_name_list()
        # テーブル名のバリデーション
        validate_non_existence(
            value=self.table_name,
            existing_list=table_name_list,
            target=self.param_names["table_name"],
        )

    def execute(self):
        # CSVファイルのインポート処理
        try:
            # CSVファイルをPolarsデータフレームに変換
            df = pl.read_csv(
                self.file_path,
                separator=self.separator,
                encoding=self.encoding,
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
            raise ProcessingError(
                error_code=ErrorCode.CSV_IMPORT_ERROR, message=message
            ) from e
        except pl.exceptions.ComputeError as e:
            message = _(
                "Failed to parse CSV file: Invalid format or encoding."
            )
            raise ProcessingError(
                error_code=ErrorCode.CSV_IMPORT_ERROR, message=message
            ) from e
        except Exception as e:
            message = _("An unexpected error occurred during CSV processing")
            raise ProcessingError(
                error_code=ErrorCode.CSV_IMPORT_ERROR, message=message
            ) from e

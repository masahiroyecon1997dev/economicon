import polars as pl

from ...exceptions import ApiError
from ...i18n.translation import gettext as _
from ...models import ImportParquetByPathRequestBody
from ...utils.validators.common import ValidationError
from ...utils.validators.files import validate_file_path
from ...utils.validators.tables_store import validate_new_table_name
from ..data.tables_store import TablesStore


class ImportParquetByPath:
    """
    PARQUETファイルパス指定でデータをインポートしてテーブルを作成するAPIクラス

    指定されたパスのPARQUETファイルを解析し、指定されたテーブル名で登録します。
    """

    def __init__(self, body: ImportParquetByPathRequestBody):
        # テーブルマネージャーの初期化
        self.tables_store = TablesStore()
        # ファイルパス
        self.file_path = body.file_path
        # テーブル名
        self.table_name = body.table_name
        # パラメータ名のマッピング
        self.param_names = {
            "file_path": "filePath",
            "table_name": "tableName",
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            validate_file_path(self.file_path, self.param_names["file_path"])
            table_name_list = self.tables_store.get_table_name_list()
            # テーブル名のバリデーション
            validate_new_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # PARQUETファイルのインポート処理
        try:
            # PARQUETファイルをPolarsデータフレームに変換
            df = pl.read_parquet(self.file_path)

            # テーブルを作成
            created_table_name = self.tables_store.store_table(
                self.table_name, df
            )

            # 結果を返す
            result = {"tableName": created_table_name}
            return result

        except pl.exceptions.NoDataError as e:
            message = _("The PARQUET file is empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.exceptions.ComputeError as e:
            message = _(
                "Failed to parse PARQUET file: Invalid format or encoding."
            )
            raise ApiError(message) from e
        except Exception as e:
            message = _(
                "An unexpected error occurred during PARQUET processing"
            )
            raise ApiError(message) from e

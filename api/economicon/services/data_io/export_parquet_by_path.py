import os

from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...models import ExportParquetByPathRequestBody
from ...utils import ProcessingError
from ...utils.validators import (
    validate_directory_path,
    validate_existence,
)
from ..data.tables_store import TablesStore


class ExportParquetByPath:
    """
    テーブルをPARQUETファイルパス指定でエクスポートするAPIクラス

    指定されたテーブル名のデータを指定されたパスにPARQUETファイルとして出力します。
    """

    def __init__(
        self,
        body: ExportParquetByPathRequestBody,
        tables_store: TablesStore,
    ):
        # テーブルマネージャーの初期化
        self.tables_store = tables_store
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
        # テーブル名のバリデーション
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
        # PARQUETファイルのエクスポート処理
        try:
            # テーブルを取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            file_path = os.path.join(self.directory_path, self.file_name)

            # PARQUETファイルに書き込み
            df.write_parquet(file_path)

            # 結果を返す
            result = {"filePath": file_path}
            return result

        except KeyError as e:
            message = _("Table does not exist: {}").format(self.table_name)
            raise ProcessingError(
                error_code=ErrorCode.PARQUET_EXPORT_ERROR, message=message
            ) from e
        except PermissionError as e:
            message = _(
                "Permission denied: Cannot write to the specified path."
            )
            raise ProcessingError(
                error_code=ErrorCode.PARQUET_EXPORT_ERROR, message=message
            ) from e
        except Exception as e:
            message = _(
                "An unexpected error occurred during PARQUET export processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.PARQUET_EXPORT_ERROR, message=message
            ) from e

import polars as pl

from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...models import ImportFileRequestBody
from ...utils import ProcessingError
from ...utils.validators import (
    validate_file_path,
    validate_non_existence,
)
from ..data.tables_store import TablesStore


class ImportExcel:
    """
    Excelファイルパス指定でデータをインポートしてテーブルを作成するAPIクラス

    指定されたパスのExcelファイルを解析し、指定されたテーブル名で登録します。
    sheet_name を指定した場合はそのシートを、省略や null の場合は先頭シートを読み込みます。
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
        # シート名（None または空文字の場合は先頭シート）
        self.sheet_name = body.sheet_name or None
        # パラメータ名のマッピング
        self.param_names = {
            "file_path": "filePath",
            "table_name": "tableName",
            "sheet_name": "sheetName",
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
        # Excelファイルのインポート処理
        try:
            # ExcelファイルをPolarsデータフレームに変換
            if self.sheet_name:
                df = pl.read_excel(self.file_path, sheet_name=self.sheet_name)
            else:
                df = pl.read_excel(self.file_path)

            # テーブルを作成
            created_table_name = self.tables_store.store_table(
                self.table_name, df
            )

            # 結果を返す
            result = {"tableName": created_table_name}
            return result

        except pl.exceptions.NoDataError as e:
            message = _("The EXCEL file is empty or contains no valid data.")
            raise ProcessingError(
                error_code=ErrorCode.EXCEL_IMPORT_ERROR, message=message
            ) from e
        except pl.exceptions.ComputeError as e:
            message = _(
                "Failed to parse EXCEL file: Invalid format or encoding."
            )
            raise ProcessingError(
                error_code=ErrorCode.EXCEL_IMPORT_ERROR, message=message
            ) from e
        except Exception as e:
            message = _("An unexpected error occurred during EXCEL processing")
            raise ProcessingError(
                error_code=ErrorCode.EXCEL_IMPORT_ERROR, message=message
            ) from e

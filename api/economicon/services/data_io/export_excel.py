import os

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import ExportFileRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_directory_path,
    validate_existence,
)

# 拡張子
_EXTENSION = ".xlsx"
# デフォルトシート名
_DEFAULT_SHEET = "Sheet1"


class ExportExcel:
    """
    テーブルを Excel ファイルにエクスポートする API クラス

    指定されたテーブル名のデータを XLSX ファイルとして出力します。
    シート名を指定できます。
    """

    def __init__(
        self,
        body: ExportFileRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.directory_path = body.directory_path
        # file_name には拡張子を含まない
        self.file_name = body.file_name
        self.sheet_name = body.sheet_name or _DEFAULT_SHEET
        self.param_names = {
            "table_name": "tableName",
            "directory_path": "directoryPath",
            "file_name": "fileName",
        }

    def validate(self):
        # 対象テーブルが存在することを検証
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

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            file_path = os.path.join(
                self.directory_path, self.file_name + _EXTENSION
            )

            df.write_excel(file_path, worksheet=self.sheet_name)

            return {"filePath": file_path}

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
                "An unexpected error occurred during EXCEL export processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.EXCEL_EXPORT_ERROR,
                message=message,
                detail=str(e),
            ) from e

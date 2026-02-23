import io
import os

from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...models import ExportFileRequestBody
from ...utils import ProcessingError
from ...utils.validators import (
    validate_directory_path,
    validate_existence,
)
from ..data.tables_store import TablesStore

# 拡張子
_EXTENSION = ".csv"

# CsvEncoding 値 → Python コーデック名のマッピング
_ENCODING_MAP = {
    "utf8": "utf-8",
    "latin1": "latin-1",
    "ascii": "ascii",
    "gbk": "gbk",
    "windows-1252": "windows-1252",
    "shift_jis": "cp932",
}


class ExportCsv:
    """
    テーブルを CSV ファイルにエクスポートする API クラス

    指定されたテーブル名のデータを CSV ファイルとして출力します。
    区切り文字およびヘッダ有無を指定できます。
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
        self.separator = body.separator
        self.encoding = body.encoding
        self.include_header = body.include_header
        self.param_names = {
            "table_name": "tableName",
            "directory_path": "directoryPath",
            "file_name": "fileName",
            "separator": "separator",
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

            # StringIO 経由で書き出し、指定エンコーディングで保存
            buffer = io.StringIO()
            df.write_csv(
                buffer,
                separator=self.separator,
                include_header=self.include_header,
            )
            python_encoding = _ENCODING_MAP.get(self.encoding, self.encoding)
            with open(file_path, "w", encoding=python_encoding) as f:
                f.write(buffer.getvalue())

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
                "An unexpected error occurred during CSV export processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.CSV_EXPORT_ERROR,
                message=message,
                detail=str(e),
            ) from e

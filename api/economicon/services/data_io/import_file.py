from pathlib import Path

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import ImportFileRequestBody
from economicon.services.data.settings_store import SettingsStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.data_io.common import update_last_opened_path
from economicon.services.data_io.import_csv import ImportCsv
from economicon.services.data_io.import_excel import ImportExcel
from economicon.services.data_io.import_parquet import ImportParquet
from economicon.utils import ProcessingError

_CSV_EXTENSIONS = {".csv", ".tsv"}
_EXCEL_EXTENSIONS = {".xlsx", ".xls"}
_PARQUET_EXTENSIONS = {".parquet"}


class ImportFile:
    """適切なインポーターを選択してファイルを取り込む。"""

    def __init__(
        self,
        body: ImportFileRequestBody,
        tables_store: TablesStore,
        settings_store: SettingsStore,
    ) -> None:
        self.body = body
        self.tables_store = tables_store
        self.settings_store = settings_store
        self._delegate: ImportCsv | ImportExcel | ImportParquet | None = (
            None
        )

    def _get_delegate(self) -> ImportCsv | ImportExcel | ImportParquet:
        if self._delegate is not None:
            return self._delegate

        suffix = Path(self.body.file_path).suffix.lower()
        if suffix in _CSV_EXTENSIONS:
            self._delegate = ImportCsv(self.body, self.tables_store)
            return self._delegate
        if suffix in _EXCEL_EXTENSIONS:
            self._delegate = ImportExcel(self.body, self.tables_store)
            return self._delegate
        if suffix in _PARQUET_EXTENSIONS:
            self._delegate = ImportParquet(self.body, self.tables_store)
            return self._delegate

        message = _(
            "Unsupported file type: '{suffix}'. "
            "Supported types: .csv, .tsv, .xlsx, .xls, .parquet"
        ).format(suffix=suffix)
        raise ProcessingError(
            error_code=ErrorCode.UNSUPPORTED_FILE_TYPE,
            message=message,
        )

    def validate(self) -> None:
        self._get_delegate().validate()

    def execute(self) -> dict:
        result = self._get_delegate().execute()
        update_last_opened_path(
            self.settings_store,
            str(Path(self.body.file_path).parent),
        )
        return result

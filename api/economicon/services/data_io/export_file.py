from economicon.schemas import ExportFileRequestBody
from economicon.services.data.settings_store import SettingsStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.data_io.common import update_last_opened_path
from economicon.services.data_io.export_csv import ExportCsv
from economicon.services.data_io.export_excel import ExportExcel
from economicon.services.data_io.export_parquet import ExportParquet

_EXPORT_FORMAT_MAP = {
    "csv": ExportCsv,
    "excel": ExportExcel,
    "parquet": ExportParquet,
}


class ExportFile:
    """適切なエクスポーターを選択してファイルを書き出す。"""

    def __init__(
        self,
        body: ExportFileRequestBody,
        tables_store: TablesStore,
        settings_store: SettingsStore,
    ) -> None:
        self.body = body
        self.tables_store = tables_store
        self.settings_store = settings_store
        self._delegate: ExportCsv | ExportExcel | ExportParquet | None = (
            None
        )

    def _get_delegate(self) -> ExportCsv | ExportExcel | ExportParquet:
        if self._delegate is None:
            cls = _EXPORT_FORMAT_MAP[self.body.format]
            self._delegate = cls(self.body, self.tables_store)
        return self._delegate

    def validate(self) -> None:
        self._get_delegate().validate()

    def execute(self) -> dict:
        result = self._get_delegate().execute()
        update_last_opened_path(
            self.settings_store,
            str(self.body.directory_path),
        )
        return result

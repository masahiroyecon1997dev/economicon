import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import (
    COMMON_ERROR_RESPONSES,
    ExportFileRequestBody,
    ExportFileResult,
    ImportFileRequestBody,
    ImportFileResult,
    SuccessResponse,
)
from economicon.services.data.dependencies import (
    SettingsStoreDep,
    TablesStoreDep,
)
from economicon.services.data.tables_store import TablesStore
from economicon.services.data_io.export_csv import ExportCsv
from economicon.services.data_io.export_excel import ExportExcel
from economicon.services.data_io.export_parquet import ExportParquet
from economicon.services.data_io.import_csv import ImportCsv
from economicon.services.data_io.import_excel import ImportExcel
from economicon.services.data_io.import_parquet import ImportParquet
from economicon.services.operation import run_operation
from economicon.utils import create_success_response, logger
from economicon.utils.exceptions import ProcessingError

router = APIRouter(
    prefix="/data",
    tags=["data"],
    responses=COMMON_ERROR_RESPONSES,
)

# サポートする拡張子と対応するインポーター
_CSV_EXTENSIONS = {".csv", ".tsv"}
_EXCEL_EXTENSIONS = {".xlsx", ".xls"}
_PARQUET_EXTENSIONS = {".parquet"}

# format 値からサービスクラスへのマッピング
_EXPORT_FORMAT_MAP = {
    "csv": ExportCsv,
    "excel": ExportExcel,
    "parquet": ExportParquet,
}


def get_import_api(
    body: ImportFileRequestBody,
    tables_store: TablesStore,
) -> ImportCsv | ImportExcel | ImportParquet:
    """拡張子に基づいて適切なインポート API クラスを返す。

    Parameters
    ----------
    body : ImportFileRequestBody
        統合インポートリクエストボディ
    tables_store : TablesStore
        テーブルストア

    Returns
    -------
    ImportCsv | ImportExcel | ImportParquet
        拡張子に対応するインポーター

    Raises
    ------
    ProcessingError
        サポートされていない拡張子の場合
    """
    suffix = Path(body.file_path).suffix.lower()
    if suffix in _CSV_EXTENSIONS:
        return ImportCsv(body, tables_store)
    if suffix in _EXCEL_EXTENSIONS:
        return ImportExcel(body, tables_store)
    if suffix in _PARQUET_EXTENSIONS:
        return ImportParquet(body, tables_store)
    message = _(
        "Unsupported file type: '{suffix}'. "
        "Supported types: .csv, .tsv, .xlsx, .xls, .parquet"
    ).format(suffix=suffix)
    raise ProcessingError(
        error_code=ErrorCode.UNSUPPORTED_FILE_TYPE, message=message
    )


@router.post(
    "/import",
    response_model=SuccessResponse[ImportFileResult],
)
async def import_file(
    request: Request,
    body: ImportFileRequestBody,
    tables_store: TablesStoreDep,
    settings_store: SettingsStoreDep,
):
    """拡張子に基づいてファイルをインポートしてテーブルを作成するエンドポイント

    対応拡張子:
    - ``.csv`` / ``.tsv`` → CSV インポーター（separator / encoding が有効）
    - ``.xlsx`` / ``.xls`` → Excel インポーター（sheet_name が有効）
    - ``.parquet``         → Parquet インポーター

    インポート成功後、ファイルの親ディレクトリを
    ``last_opened_path`` として設定ファイルに保存する。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : ImportFileRequestBody
        リクエストボディ
    tables_store : TablesStoreDep
        依存注入されたテーブルストア
    settings_store : SettingsStoreDep
        依存注入された設定ストア

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = get_import_api(body, tables_store)
    result = run_operation(api)

    # インポート成功後、最後に開いたパスを設定ファイルへ保存
    # 非クリティカルな処理のため、失敗しても本体レスポンスに影響しない
    try:
        parent_dir = str(Path(body.file_path).parent).replace(os.sep, "/")
        settings_store.update_settings(last_opened_path=parent_dir)
        settings_store.save_settings()
        logger.info(f"Updated last_opened_path: {parent_dir}")
    except Exception as e:
        logger.warning(f"Failed to update last_opened_path in settings: {e}")

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


def get_export_api(
    body: ExportFileRequestBody,
    tables_store: TablesStore,
) -> ExportCsv | ExportExcel | ExportParquet:
    """format フィールドに基づいて適切なエクスポート API クラスを返す。

    Parameters
    ----------
    body : ExportFileRequestBody
        統合エクスポートリクエストボディ
    tables_store : TablesStore
        テーブルストア

    Returns
    -------
    ExportCsv | ExportExcel | ExportParquet
        format に対応するエクスポーター
    """
    cls = _EXPORT_FORMAT_MAP[body.format]
    return cls(body, tables_store)


@router.post(
    "/export",
    response_model=SuccessResponse[ExportFileResult],
)
async def export_file(
    request: Request,
    body: ExportFileRequestBody,
    tables_store: TablesStoreDep,
):
    """format に基づいてテーブルをファイルにエクスポートするエンドポイント

    対応形式：
    - ``csv``     → CSV エクスポーター（separator / include_header が有効）
    - ``excel``   → Excel エクスポーター（sheet_name / include_header が有効）
    - ``parquet`` → Parquet エクスポーター

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : ExportFileRequestBody
        リクエストボディ
    tables_store : TablesStoreDep
        依存注入されたテーブルストア

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = get_export_api(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

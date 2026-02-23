from pathlib import Path

from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..core.enums import ErrorCode
from ..i18n.translation import gettext as _
from ..models import (
    ExportCsvByPathRequestBody,
    ExportCsvByPathResult,
    ExportExcelByPathRequestBody,
    ExportExcelByPathResult,
    ExportParquetByPathRequestBody,
    ExportParquetByPathResult,
    ImportByPathRequestBody,
    ImportByPathResult,
    SuccessResponse,
)
from ..services.data.dependencies import TablesStoreDep
from ..services.data.tables_store import TablesStore
from ..services.data_io.export_csv_by_path import ExportCsvByPath
from ..services.data_io.export_excel_by_path import ExportExcelByPath
from ..services.data_io.export_parquet_by_path import ExportParquetByPath
from ..services.data_io.import_csv_by_path import ImportCsvByPath
from ..services.data_io.import_excel_by_path import ImportExcelByPath
from ..services.data_io.import_parquet_by_path import ImportParquetByPath
from ..services.operation import run_operation
from ..utils import create_success_response
from ..utils.exceptions import ProcessingError

router = APIRouter(prefix="/data", tags=["data"])

# サポートする拡張子と対応するインポーター
_CSV_EXTENSIONS = {".csv", ".tsv"}
_EXCEL_EXTENSIONS = {".xlsx", ".xls"}
_PARQUET_EXTENSIONS = {".parquet"}


def get_import_api(
    body: ImportByPathRequestBody,
    tables_store: TablesStore,
) -> ImportCsvByPath | ImportExcelByPath | ImportParquetByPath:
    """拡張子に基づいて適切なインポート API クラスを返す。

    Parameters
    ----------
    body : ImportByPathRequestBody
        統合インポートリクエストボディ
    tables_store : TablesStore
        テーブルストア

    Returns
    -------
    ImportCsvByPath | ImportExcelByPath | ImportParquetByPath
        拡張子に対応するインポーター

    Raises
    ------
    ProcessingError
        サポートされていない拡張子の場合
    """
    suffix = Path(body.file_path).suffix.lower()
    if suffix in _CSV_EXTENSIONS:
        return ImportCsvByPath(body, tables_store)
    if suffix in _EXCEL_EXTENSIONS:
        return ImportExcelByPath(body, tables_store)
    if suffix in _PARQUET_EXTENSIONS:
        return ImportParquetByPath(body, tables_store)
    message = _(
        "Unsupported file type: '{suffix}'. "
        "Supported types: .csv, .tsv, .xlsx, .xls, .parquet"
    ).format(suffix=suffix)
    raise ProcessingError(
        error_code=ErrorCode.UNSUPPORTED_FILE_TYPE, message=message
    )


@router.post(
    "/import",
    response_model=SuccessResponse[ImportByPathResult],
)
async def import_file(
    request: Request,
    body: ImportByPathRequestBody,
    tables_store: TablesStoreDep,
):
    """拡張子に基づいてファイルをインポートしてテーブルを作成するエンドポイント

    対応拡張子:
    - ``.csv`` / ``.tsv`` → CSV インポーター（separator / encoding が有効）
    - ``.xlsx`` / ``.xls`` → Excel インポーター（sheet_name が有効）
    - ``.parquet``         → Parquet インポーター

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : ImportByPathRequestBody
        リクエストボディ
    tables_store : TablesStoreDep
        依存注入されたテーブルストア

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = get_import_api(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/export-csv-by-path",
    response_model=SuccessResponse[ExportCsvByPathResult],
)
async def export_csv_by_path(
    request: Request,
    body: ExportCsvByPathRequestBody,
    tables_store: TablesStoreDep,
):
    """テーブルをCSVファイルにパス指定でエクスポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ExportCsvByPathRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = ExportCsvByPath(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/export-excel-by-path",
    response_model=SuccessResponse[ExportExcelByPathResult],
)
async def export_excel_by_path(
    request: Request,
    body: ExportExcelByPathRequestBody,
    tables_store: TablesStoreDep,
):
    """テーブルをExcelファイルにパス指定でエクスポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ExportExcelByPathRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = ExportExcelByPath(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/export-parquet-by-path",
    response_model=SuccessResponse[ExportParquetByPathResult],
)
async def export_parquet_by_path(
    request: Request,
    body: ExportParquetByPathRequestBody,
    tables_store: TablesStoreDep,
):
    """テーブルをParquetファイルにパス指定でエクスポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ExportParquetByPathRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = ExportParquetByPath(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

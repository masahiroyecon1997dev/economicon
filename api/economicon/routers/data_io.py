from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..models import (
    ExportCsvByPathRequestBody,
    ExportExcelByPathRequestBody,
    ExportParquetByPathRequestBody,
    ImportCsvByPathRequestBody,
    ImportExcelByPathRequestBody,
    ImportParquetByPathRequestBody,
)
from ..services.data_io.export_csv_by_path import ExportCsvByPath
from ..services.data_io.export_excel_by_path import ExportExcelByPath
from ..services.data_io.export_parquet_by_path import ExportParquetByPath
from ..services.data_io.import_csv_by_path import ImportCsvByPath
from ..services.data_io.import_excel_by_path import ImportExcelByPath
from ..services.data_io.import_parquet_by_path import ImportParquetByPath
from ..services.operation import run_operation
from ..utils import create_success_response

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/import-csv-by-path")
async def import_csv_by_path(
    request: Request, body: ImportCsvByPathRequestBody
):
    """パス指定でCSVファイルをインポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportCsvByPathRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = ImportCsvByPath(body)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/import-excel-by-path")
async def import_excel_by_path(
    request: Request, body: ImportExcelByPathRequestBody
):
    """EXCELファイルをパス指定でインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportExcelByPathRequestBody
        リクエストボディ
        - filePath: EXCELファイルのパス
        - tableName: 作成するテーブル名
        - sheetName: シート名（オプション）

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = ImportExcelByPath(body)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/import-parquet-by-path")
async def import_parquet_by_path(
    request: Request, body: ImportParquetByPathRequestBody
):
    """PARQUETファイルをパス指定でインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportParquetByPathRequestBody
        リクエストボディ
        - filePath: PARQUETファイルのパス
        - tableName: 作成するテーブル名

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = ImportParquetByPath(body)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/export-csv-by-path")
async def export_csv_by_path(
    request: Request, body: ExportCsvByPathRequestBody
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
    api = ExportCsvByPath(body)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/export-excel-by-path")
async def export_excel_by_path(
    request: Request, body: ExportExcelByPathRequestBody
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
    api = ExportExcelByPath(body)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/export-parquet-by-path")
async def export_parquet_by_path(
    request: Request, body: ExportParquetByPathRequestBody
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
    api = ExportParquetByPath(body)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

from fastapi import APIRouter, File, Request, UploadFile
from fastapi import status as http_status

from ..schemas import (ExportCsvByPathRequest, ExportExcelByPathRequest,
                       ExportParquetByPathRequest, ImportCsvByPathRequest,
                       ImportExcelByPathRequest, ImportParquetByPathRequest)
from ..services.export_csv_by_path import export_csv_by_path
from ..services.export_excel_by_path import export_excel_by_path
from ..services.export_parquet_by_path import export_parquet_by_path
from ..services.import_csv_by_file import import_csv_by_file
from ..services.import_csv_by_path import import_csv_by_path
from ..services.import_excel_by_file import import_excel_by_file
from ..services.import_excel_by_path import import_excel_by_path
from ..services.import_parquet_by_file import import_parquet_by_file
from ..services.import_parquet_by_path import import_parquet_by_path
from ..services.import_tsv_by_file import import_tsv_by_file
from ..utils import create_log_api_request, create_success_response

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/import-csv-by-file")
async def import_csv_by_file_endpoint(request: Request,
                                      file: UploadFile = File(...)):
    """アップロードされたCSVファイルをインポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    file : UploadFile
        アップロードされたファイル

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = import_csv_by_file(
        file_data=file.file,
        file_name=file.filename
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/import-csv-by-path")
async def import_csv_by_path_endpoint(request: Request,
                                      body: ImportCsvByPathRequest):
    """パス指定でCSVファイルをインポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportCsvByPathRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = import_csv_by_path(
        file_path=body.filePath,
        table_name=body.tableName,
        separator=body.separator
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/import-tsv-by-file")
async def import_tsv_by_file_endpoint(request: Request,
                                      file: UploadFile = File(...)):
    """アップロードされたTSVファイルをインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    file : UploadFile
        アップロードされたTSVファイル

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = import_tsv_by_file(
        file_data=file.file,
        file_name=file.filename
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/import-excel-by-file")
async def import_excel_by_file_endpoint(request: Request,
                                        file: UploadFile = File(...)):
    """アップロードされたExcelファイルをインポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    file : UploadFile
        アップロードされたファイル

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = import_excel_by_file(
        file_data=file.file,
        file_name=file.filename
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/import-excel-by-path")
async def import_excel_by_path_endpoint(request: Request,
                                        body: ImportExcelByPathRequest):
    """EXCELファイルをパス指定でインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportExcelByPathRequest
        リクエストボディ
        - filePath: EXCELファイルのパス
        - tableName: 作成するテーブル名
        - sheetName: シート名（オプション）

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = import_excel_by_path(
        file_path=body.filePath,
        table_name=body.tableName,
        sheet_name=body.sheetName
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/import-parquet-by-file")
async def import_parquet_by_file_endpoint(request: Request,
                                          file: UploadFile = File(...)):
    """アップロードされたParquetファイルをインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    file : UploadFile
        アップロードされたParquetファイル

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = import_parquet_by_file(
        file_data=file.file,
        file_name=file.filename
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/import-parquet-by-path")
async def import_parquet_by_path_endpoint(request: Request,
                                          body: ImportParquetByPathRequest):
    """PARQUETファイルをパス指定でインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportParquetByPathRequest
        リクエストボディ
        - filePath: PARQUETファイルのパス
        - tableName: 作成するテーブル名

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = import_parquet_by_path(
        file_path=body.filePath,
        table_name=body.tableName
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/export-csv-by-path")
async def export_csv_by_path_endpoint(request: Request,
                                      body: ExportCsvByPathRequest):
    """テーブルをCSVファイルにパス指定でエクスポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ExportCsvByPathRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = export_csv_by_path(
        table_name=body.tableName,
        directory_path=body.directoryPath,
        file_name=body.fileName,
        separator=body.separator
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/export-excel-by-path")
async def export_excel_by_path_endpoint(request: Request,
                                        body: ExportExcelByPathRequest):
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
    create_log_api_request(request)

    result = export_excel_by_path(
        table_name=body.tableName,
        directory_path=body.directoryPath,
        file_name=body.fileName
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/export-parquet-by-path")
async def export_parquet_by_path_endpoint(request: Request,
                                          body: ExportParquetByPathRequest):
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
    create_log_api_request(request)

    result = export_parquet_by_path(
        table_name=body.tableName,
        directory_path=body.directoryPath,
        file_name=body.fileName
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

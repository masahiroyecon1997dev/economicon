from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
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
from economicon.services.data_io.export_file import ExportFile
from economicon.services.data_io.import_file import ImportFile
from economicon.services.operation import run_operation
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/data",
    tags=["data"],
    responses=COMMON_ERROR_RESPONSES,
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
    ``last_opened_path`` としてメモリ上の設定に反映する。
    ファイルへの保存はアプリ終了時に一括して行われる。

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
    api = ImportFile(body, tables_store, settings_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/export",
    response_model=SuccessResponse[ExportFileResult],
)
async def export_file(
    request: Request,
    body: ExportFileRequestBody,
    tables_store: TablesStoreDep,
    settings_store: SettingsStoreDep,
):
    """format に基づいてテーブルをファイルにエクスポートするエンドポイント

    対応形式：
    - ``csv``     → CSV エクスポーター（separator / include_header が有効）
    - ``excel``   → Excel エクスポーター（sheet_name / include_header が有効）
    - ``parquet`` → Parquet エクスポーター

    エクスポート成功後、出力先ディレクトリを
    ``last_opened_path`` としてメモリ上の設定に反映する。
    ファイルへの保存はアプリ終了時に一括して行われる。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : ExportFileRequestBody
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
    api = ExportFile(body, tables_store, settings_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

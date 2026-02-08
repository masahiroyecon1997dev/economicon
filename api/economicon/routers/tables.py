from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..schemas import (
    CreateJoinTableRequest,
    CreateSimulationDataTableRequest,
    CreateTableRequest,
    CreateUnionTableRequest,
    DeleteTableRequest,
    DuplicateTableRequest,
    FetchDataToArrowRequest,
    FetchDataToJsonRequest,
    FilterSingleConditionRequest,
    InputCellDataRequest,
    RenameTableRequest,
)
from ..services.tables.clear_tables import clear_tables
from ..services.tables.create_join_table import create_join_table
from ..services.tables.create_simulation_data_table import (
    create_simulation_data_table,
)
from ..services.tables.create_table import create_table
from ..services.tables.create_union_table import create_union_table
from ..services.tables.delete_table import delete_table
from ..services.tables.duplicate_table import duplicate_table
from ..services.tables.fetch_data_to_arrow import fetch_data_to_arrow
from ..services.tables.fetch_data_to_json import fetch_data_to_json
from ..services.tables.filter_single_condition import filter_single_condition
from ..services.tables.get_table_list import get_table_list
from ..services.tables.input_cell_data import input_cell_data
from ..services.tables.rename_table import rename_table
from ..utils import (
    create_log_api_request,
    create_success_binary_response,
    create_success_response,
)

router = APIRouter(prefix="/table", tags=["table"])


@router.post("/create")
async def create_table_endpoint(request: Request, body: CreateTableRequest):
    """テーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateTableRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    result = create_table(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/create-join")
async def create_join_table_endpoint(
    request: Request, body: CreateJoinTableRequest
):
    """結合テーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateJoinTableRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    result = create_join_table(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/create-union")
async def create_union_table_endpoint(
    request: Request, body: CreateUnionTableRequest
):
    """ユニオンテーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateUnionTableRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    result = create_union_table(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/create-simulation-data")
async def create_simulation_data_table_endpoint(
    request: Request, body: CreateSimulationDataTableRequest
):
    """シミュレーションデータテーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateSimulationDataTableRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    result = create_simulation_data_table(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/delete")
async def delete_table_endpoint(request: Request, body: DeleteTableRequest):
    """テーブルを削除するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DeleteTableRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = delete_table(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/duplicate")
async def duplicate_table_endpoint(
    request: Request, body: DuplicateTableRequest
):
    """テーブルを複製するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DuplicateTableRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = duplicate_table(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/rename")
async def rename_table_endpoint(request: Request, body: RenameTableRequest):
    """
    テーブル名変更エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RenameTableRequest
        リクエストボディ
        - oldTableName: 旧テーブル名
        - newTableName: 新テーブル名

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = rename_table(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.get("/get-list")
async def get_table_list_endpoint(request: Request):
    """テーブルリストを取得するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = get_table_list()

    return create_success_response(http_status.HTTP_200_OK, result)


@router.delete("/clear-all")
async def clear_tables_endpoint(request: Request):
    """全テーブルをクリアするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    result = clear_tables()

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/fetch-data-to-json")
async def fetch_data_to_json_endpoint(
    request: Request, body: FetchDataToJsonRequest
):
    """データをJSON形式で取得するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FetchDataToJsonRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = fetch_data_to_json(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/fetch-data-to-arrow")
async def fetch_data_to_arrow_endpoint(
    request: Request, body: FetchDataToArrowRequest
):
    """データをApache Arrow IPC形式で取得するエンドポイント

    仮想スクロール用のチャンク取得API。
    Apache Arrow IPC形式のバイナリデータ（Base64エンコード）を返します。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FetchDataToArrowRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果（Arrow IPC形式のBase64エンコードされたバイナリを含む）
    """
    create_log_api_request(request)

    result = fetch_data_to_arrow(**body.model_dump())

    return create_success_binary_response(
        http_status.HTTP_200_OK, result, "application/octet-stream"
    )


@router.post("/input-cell-data")
async def input_cell_data_endpoint(
    request: Request, body: InputCellDataRequest
):
    """セルデータ入力エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : InputCellDataRequest
        リクエストボディ
        - tableName: テーブル名
        - columnName: 列名
        - rowIndex: 行インデックス
        - newValue: 新しい値

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = input_cell_data(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/filter-single-condition")
async def filter_single_condition_endpoint(
    request: Request, body: FilterSingleConditionRequest
):
    """単一条件フィルタリングを実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FilterSingleConditionRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = filter_single_condition(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)

from typing import cast

from fastapi import APIRouter, Request, Response
from fastapi import status as http_status

from economicon.models import (
    COMMON_ERROR_RESPONSES,
    ClearTablesResult,
    CreateJoinTableRequestBody,
    CreateJoinTableResult,
    CreateSimulationDataTableRequestBody,
    CreateSimulationDataTableResult,
    CreateUnionTableRequestBody,
    CreateUnionTableResult,
    DeleteTableRequestBody,
    DeleteTableResult,
    DuplicateTableRequestBody,
    DuplicateTableResult,
    FetchDataToArrowRequestBody,
    FetchDataToJsonRequestBody,
    FetchDataToJsonResult,
    FilterSingleConditionRequestBody,
    FilterSingleConditionResult,
    GetTableListResult,
    InputCellDataRequestBody,
    InputCellDataResult,
    RenameTableRequestBody,
    RenameTableResult,
    SuccessResponse,
)
from economicon.services.data.dependencies import TablesStoreDep
from economicon.services.operation import run_operation
from economicon.services.tables.clear_tables import ClearTables
from economicon.services.tables.create_join_table import CreateJoinTable
from economicon.services.tables.create_simulation_data_table import (
    CreateSimulationDataTable,
)
from economicon.services.tables.create_union_table import CreateUnionTable
from economicon.services.tables.delete_table import DeleteTable
from economicon.services.tables.duplicate_table import DuplicateTable
from economicon.services.tables.fetch_data_to_arrow import FetchDataToArrow
from economicon.services.tables.fetch_data_to_json import FetchDataToJson
from economicon.services.tables.filter_single_condition import (
    FilterSingleCondition,
)
from economicon.services.tables.get_table_list import GetTableList
from economicon.services.tables.input_cell_data import InputCellData
from economicon.services.tables.rename_table import RenameTable
from economicon.utils import (
    create_success_response,
)

router = APIRouter(
    prefix="/table",
    tags=["table"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post(
    "/create-join", response_model=SuccessResponse[CreateJoinTableResult]
)
async def create_join_table(
    request: Request,
    body: CreateJoinTableRequestBody,
    tables_store: TablesStoreDep,
):
    """結合テーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateJoinTableRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = CreateJoinTable(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/create-union", response_model=SuccessResponse[CreateUnionTableResult]
)
async def create_union_table(
    request: Request,
    body: CreateUnionTableRequestBody,
    tables_store: TablesStoreDep,
):
    """ユニオンテーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateUnionTableRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = CreateUnionTable(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/create-simulation-data",
    response_model=SuccessResponse[CreateSimulationDataTableResult],
)
async def create_simulation_data_table(
    request: Request,
    body: CreateSimulationDataTableRequestBody,
    tables_store: TablesStoreDep,
):
    """シミュレーションデータテーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateSimulationDataTableRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = CreateSimulationDataTable(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/delete", response_model=SuccessResponse[DeleteTableResult])
async def delete_table(
    request: Request,
    body: DeleteTableRequestBody,
    tables_store: TablesStoreDep,
):
    """テーブルを削除するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DeleteTableRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = DeleteTable(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/duplicate", response_model=SuccessResponse[DuplicateTableResult]
)
async def duplicate_table(
    request: Request,
    body: DuplicateTableRequestBody,
    tables_store: TablesStoreDep,
):
    """テーブルを複製するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DuplicateTableRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = DuplicateTable(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/rename", response_model=SuccessResponse[RenameTableResult])
async def rename_table(
    request: Request,
    body: RenameTableRequestBody,
    tables_store: TablesStoreDep,
):
    """
    テーブル名変更エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RenameTableRequestBody
        リクエストボディ
        - oldTableName: 旧テーブル名
        - newTableName: 新テーブル名

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = RenameTable(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.get("/get-list", response_model=SuccessResponse[GetTableListResult])
async def get_table_list(
    request: Request,
    tables_store: TablesStoreDep,
):
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
    # ビジネスロジックの実行
    api = GetTableList(tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.delete("/clear-all", response_model=SuccessResponse[ClearTablesResult])
async def clear_tables(
    request: Request,
    tables_store: TablesStoreDep,
):
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
    # ビジネスロジックの実行
    api = ClearTables(tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/fetch-data-to-json",
    response_model=SuccessResponse[FetchDataToJsonResult],
)
async def fetch_data_to_json(
    request: Request,
    body: FetchDataToJsonRequestBody,
    tables_store: TablesStoreDep,
):
    """データをJSON形式で取得するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FetchDataToJsonRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = FetchDataToJson(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/fetch-data-to-arrow",
    response_class=Response,
    responses={
        200: {
            "content": {"application/vnd.apache.arrow.stream": {}},
            "description": (
                "Apache Arrow IPC ファイル形式の生バイナリ。"
                "スキーマメタデータに totalRows / startRow / endRow / "
                "tableName を含む。"
            ),
        }
    },
)
async def fetch_data_to_arrow(
    request: Request,
    body: FetchDataToArrowRequestBody,
    tables_store: TablesStoreDep,
) -> Response:
    """データをApache Arrow IPC形式の生バイナリで返すエンドポイント

    仮想スクロール用のチャンク取得API。
    JSON包装なしでArrow IPC形式生バイナリを直接返す。
    メタデータ（totalRows/startRow/endRow/tableName）は
    Arrowスキーマメタデータに埋め込む。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FetchDataToArrowRequestBody
        リクエストボディ

    Returns
    -------
    Response
        Arrow IPC形式生バイナリ
    """
    api = FetchDataToArrow(body, tables_store)
    arrow_bytes = cast(bytes, run_operation(api))
    return Response(
        content=arrow_bytes,
        media_type="application/vnd.apache.arrow.stream",
    )


@router.post(
    "/input-cell-data", response_model=SuccessResponse[InputCellDataResult]
)
async def input_cell_data(
    request: Request,
    body: InputCellDataRequestBody,
    tables_store: TablesStoreDep,
):
    """セルデータ入力エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : InputCellDataRequestBody
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
    # ビジネスロジックの実行
    api = InputCellData(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/filter-single-condition",
    response_model=SuccessResponse[FilterSingleConditionResult],
)
async def filter_single_condition(
    request: Request,
    body: FilterSingleConditionRequestBody,
    tables_store: TablesStoreDep,
):
    """単一条件フィルタリングを実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FilterSingleConditionRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = FilterSingleCondition(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.models import (
    AddColumnRequestBody,
    AddColumnResult,
    AddDummyColumnRequestBody,
    AddDummyColumnResult,
    AddLagLeadColumnRequestBody,
    AddLagLeadColumnResult,
    AddSimulationColumnRequestBody,
    AddSimulationColumnResult,
    CalculateColumnRequestBody,
    CalculateColumnResult,
    DeleteColumnRequestBody,
    DeleteColumnResult,
    DuplicateColumnRequestBody,
    DuplicateColumnResult,
    GetColumnListRequestBody,
    GetColumnListResult,
    RenameColumnRequestBody,
    RenameColumnResult,
    SortColumnsRequestBody,
    SortColumnsResult,
    SuccessResponse,
    TransformColumnRequestBody,
    TransformColumnResult,
)

# 各ビジネスロジック（既存のpython_apis）
from economicon.services.columns.add_column import AddColumn
from economicon.services.columns.add_dummy_column import AddDummyColumn
from economicon.services.columns.add_lag_lead_column import AddLagLeadColumn
from economicon.services.columns.add_simulation_column import (
    AddSimulationColumn,
)
from economicon.services.columns.calculate_column import CalculateColumn
from economicon.services.columns.delete_column import DeleteColumn
from economicon.services.columns.duplicate_column import DuplicateColumn
from economicon.services.columns.get_column_list import GetColumnList
from economicon.services.columns.rename_column import RenameColumn
from economicon.services.columns.sort_columns import SortColumns
from economicon.services.columns.transform_column import TransformColumn
from economicon.services.data.dependencies import TablesStoreDep
from economicon.services.operation import run_operation
from economicon.utils import create_success_response

# ルーターの定義（ここで共通のprefixとtagをつけておくと便利！）
router = APIRouter(prefix="/column", tags=["column"])


@router.post("/add", response_model=SuccessResponse[AddColumnResult])
async def add_column(
    request: Request,
    body: AddColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """カラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = AddColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/add-dummy", response_model=SuccessResponse[AddDummyColumnResult]
)
async def add_dummy_column(
    request: Request,
    body: AddDummyColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """ダミー変数カラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddDummyColumnRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = AddDummyColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/delete", response_model=SuccessResponse[DeleteColumnResult])
async def delete_column(
    request: Request,
    body: DeleteColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """カラムを削除するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DeleteColumnRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = DeleteColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/rename", response_model=SuccessResponse[RenameColumnResult])
async def rename_column(
    request: Request,
    body: RenameColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """
    列名変更エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RenameColumnRequestBody
        リクエストボディ
        - tableName: テーブル名
        - oldColumnName: 旧列名
        - newColumnName: 新列名

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = RenameColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/add-lag-lead", response_model=SuccessResponse[AddLagLeadColumnResult]
)
async def add_lag_lead_column(
    request: Request,
    body: AddLagLeadColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """ラグ・リードカラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddLagLeadColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """

    # ビジネスロジックの実行
    api = AddLagLeadColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/add-simulation",
    response_model=SuccessResponse[AddSimulationColumnResult],
)
async def add_simulation_column(
    request: Request,
    body: AddSimulationColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """シミュレーションカラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddSimulationColumnRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = AddSimulationColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/calculate", response_model=SuccessResponse[CalculateColumnResult]
)
async def calculate_column(
    request: Request,
    body: CalculateColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """カラム計算を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CalculateColumnRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = CalculateColumn(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/duplicate", response_model=SuccessResponse[DuplicateColumnResult]
)
async def duplicate_column(
    request: Request,
    body: DuplicateColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """カラムを複製するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DuplicateColumnRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = DuplicateColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/transform", response_model=SuccessResponse[TransformColumnResult]
)
async def transform_column(
    request: Request,
    body: TransformColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """
    列の変換処理エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : TransformColumnRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = TransformColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/get-list", response_model=SuccessResponse[GetColumnListResult])
async def get_column_list(
    request: Request,
    body: GetColumnListRequestBody,
    tables_store: TablesStoreDep,
):
    """カラムリストを取得するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : GetColumnListRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = GetColumnList(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/sort", response_model=SuccessResponse[SortColumnsResult])
async def sort_columns(
    request: Request,
    body: SortColumnsRequestBody,
    tables_store: TablesStoreDep,
):
    """
    列のソート処理エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : SortColumnsRequestBody
        リクエストボディ
        - tableName: テーブル名
        - sortColumns: ソート列情報

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = SortColumns(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

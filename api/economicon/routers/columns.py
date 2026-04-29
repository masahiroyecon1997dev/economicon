from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    AddDummyColumnRequestBody,
    AddDummyColumnResult,
    AddLagLeadColumnRequestBody,
    AddLagLeadColumnResult,
    AddPanelTimeColumnRequestBody,
    AddPanelTimeColumnResult,
    AddSimulationColumnRequestBody,
    AddSimulationColumnResult,
    CalculateColumnRequestBody,
    CalculateColumnResult,
    CastColumnRequestBody,
    CastColumnResult,
    DeleteColumnRequestBody,
    DeleteColumnResult,
    GetColumnListRequestBody,
    GetColumnListResult,
    MoveColumnRequestBody,
    MoveColumnResult,
    RenameColumnRequestBody,
    RenameColumnResult,
    SortColumnsRequestBody,
    SortColumnsResult,
    SuccessResponse,
    TransformColumnRequestBody,
    TransformColumnResult,
)

# 各ビジネスロジック（既存のpython_apis）
from economicon.services.columns.add_dummy_column import AddDummyColumn
from economicon.services.columns.add_lag_lead_column import AddLagLeadColumn
from economicon.services.columns.add_panel_time_column import (
    AddPanelTimeColumn,
)
from economicon.services.columns.add_simulation_column import (
    AddSimulationColumn,
)
from economicon.services.columns.calculate_column import CalculateColumn
from economicon.services.columns.cast_column import CastColumn
from economicon.services.columns.delete_column import DeleteColumn
from economicon.services.columns.get_column_list import GetColumnList
from economicon.services.columns.move_column import MoveColumn
from economicon.services.columns.rename_column import RenameColumn
from economicon.services.columns.sort_columns import SortColumns
from economicon.services.columns.transform_column import TransformColumn
from economicon.services.data.dependencies import TablesStoreDep
from economicon.services.operation import run_operation
from economicon.utils import create_success_response

# ルーターの定義（ここで共通のprefixとtagをつけておくと便利！）
router = APIRouter(
    prefix="/column",
    tags=["column"],
    responses=COMMON_ERROR_RESPONSES,
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


@router.post("/cast", response_model=SuccessResponse[CastColumnResult])
async def cast_column(
    request: Request,
    body: CastColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """列型変換エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CastColumnRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = CastColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post("/move", response_model=SuccessResponse[MoveColumnResult])
async def move_column(
    request: Request,
    body: MoveColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """列を指定した位置に移動するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : MoveColumnRequestBody
        リクエストボディ
        - tableName: テーブル名
        - columnName: 移動する列名
        - anchorColumnName: 挿入基準列名（null のとき末尾に移動）

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = MoveColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/add-panel-time",
    response_model=SuccessResponse[AddPanelTimeColumnResult],
)
async def add_panel_time_column(
    request: Request,
    body: AddPanelTimeColumnRequestBody,
    tables_store: TablesStoreDep,
):
    """パネル時間カラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddPanelTimeColumnRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = AddPanelTimeColumn(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )

from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..models import (
    AddColumnRequestBody,
    AddColumnResult,
    AddDummyColumnRequestBody,
    AddLagLeadColumnRequestBody,
    AddSimulationColumnRequestBody,
    CalculateColumnRequestBody,
    DeleteColumnRequestBody,
    DuplicateColumnRequestBody,
    GetColumnListRequestBody,
    RenameColumnRequestBody,
    SortColumnsRequestBody,
    SuccessResponse,
    TransformColumnRequestBody,
)

# 各ビジネスロジック（既存のpython_apis）
from ..services.columns.add_column import AddColumn
from ..services.columns.add_dummy_column import AddDummyColumn
from ..services.columns.add_lag_lead_column import AddLagLeadColumn
from ..services.columns.add_simulation_column import AddSimulationColumn
from ..services.columns.calculate_column import CalculateColumn
from ..services.columns.delete_column import DeleteColumn
from ..services.columns.duplicate_column import DuplicateColumn
from ..services.columns.get_column_list import GetColumnList
from ..services.columns.rename_column import RenameColumn
from ..services.columns.sort_columns import SortColumns
from ..services.columns.transform_column import TransformColumn
from ..services.operation import run_operation
from ..utils import create_log_api_request, create_success_response

# ルーターの定義（ここで共通のprefixとtagをつけておくと便利！）
router = APIRouter(prefix="/column", tags=["column"])


@router.post("/add", response_model=SuccessResponse[AddColumnResult])
async def add_column(request: Request, body: AddColumnRequestBody):
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
    # リクエスト受け取りログ
    create_log_api_request(request)
    # ビジネスロジックの実行
    api = AddColumn(**body.model_dump())
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/add-dummy")
async def add_dummy_column(request: Request, body: AddDummyColumnRequestBody):
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
    # リクエスト受け取りログ
    create_log_api_request(request)
    # ビジネスロジックの実行
    api = AddDummyColumn(**body.model_dump())
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/delete")
async def delete_column(request: Request, body: DeleteColumnRequestBody):
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
    create_log_api_request(request)
    api = DeleteColumn(**body.model_dump())
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/rename")
async def rename_column(request: Request, body: RenameColumnRequestBody):
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
    create_log_api_request(request)
    api = RenameColumn(**body.model_dump())
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/add-lag-lead")
async def add_lag_lead_column(
    request: Request, body: AddLagLeadColumnRequestBody
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
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    api = AddLagLeadColumn(**body.model_dump())
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/add-simulation")
async def add_simulation_column(
    request: Request, body: AddSimulationColumnRequestBody
):
    """シミュレーションカラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddSimulationColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)
    # ビジネスロジックの実行
    api = AddSimulationColumn(
        table_name=body.table_name,
        new_column_name=body.new_column_name,
        distribution=body.distribution,
    )
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/calculate")
async def calculate_column(request: Request, body: CalculateColumnRequestBody):
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
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    api = CalculateColumn(**body.model_dump())
    result = run_operation(api)

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/duplicate")
async def duplicate_column(request: Request, body: DuplicateColumnRequestBody):
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
    # リクエスト受け取りログ
    create_log_api_request(request)
    # ビジネスロジックの実行
    api = DuplicateColumn(**body.model_dump())
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/transform")
async def transform_column(request: Request, body: TransformColumnRequestBody):
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
    # リクエスト受け取りログ
    create_log_api_request(request)
    # ビジネスロジックの実行
    api = TransformColumn(**body.model_dump())
    result = run_operation(api)
    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/get-list")
async def get_column_list(request: Request, body: GetColumnListRequestBody):
    """カラムリストを取得するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : GetColumnListRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    api = GetColumnList(**body.model_dump())
    result = run_operation(api)

    return create_success_response(http_status.HTTP_200_OK, result)


@router.post("/sort")
async def sort_columns(request: Request, body: SortColumnsRequestBody):
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
    create_log_api_request(request)

    api = SortColumns(body.table_name, body.sort_columns)
    result = run_operation(api)

    return create_success_response(http_status.HTTP_200_OK, result)

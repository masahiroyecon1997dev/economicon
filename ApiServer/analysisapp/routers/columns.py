from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services import ApiError
from ..schemas import (
    AddColumnRequest,
    AddDummyColumnRequest,
    DeleteColumnRequest,
    RenameColumnRequest,
    AddLagLeadColumnRequest,
    AddSimulationColumnRequest,
    StatisticsCalculateColumnRequest,
    DataDuplicateColumnRequest,
    TransformColumnRequest
)
# 各ビジネスロジック（既存のpython_apis）
from ..services.add_column import add_column
from ..services.add_dummy_column import add_dummy_column
from ..services.delete_column import delete_column
from ..services.rename_column import rename_column
from ..services.add_lag_lead_column import add_lag_lead_column
from ..services.add_simulation_column import add_simulation_column
from ..services.calculate_column import calculate_column
from ..services.duplicate_column import duplicate_column
from ..services.transform_column import transform_column

# ルーターの定義（ここで共通のprefixとtagをつけておくと便利！）
router = APIRouter(prefix="/column", tags=["column"])

@router.post("/add")
async def add_column_endpoint(request: Request, body: AddColumnRequest):
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
    # ビジネスロジックの実行（既存のpython_apisをそのまま使用）
    result = add_column(
        table_name=body.tableName,
        new_column_name=body.newColumnName,
        add_position_column=body.addPositionColumn
    )
    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

@router.post("/add-dummy")
async def add_dummy_column_endpoint(request: Request, body: AddDummyColumnRequest):
    """ダミー変数カラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddDummyColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)
    # ビジネスロジックの実行
    result = add_dummy_column(
        table_name=body.tableName,
        source_column_name=body.sourceColumnName,
        dummy_column_name=body.dummyColumnName,
        target_value=body.targetValue
    )
    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

@router.post("/delete")
async def delete_column_endpoint(request: Request, body: DeleteColumnRequest):
    """カラムを削除するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DeleteColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)
    result = delete_column(
        table_name=body.tableName,
        column_name=body.columnName
    )
    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

@router.post("/rename")
async def rename_column_endpoint(request: Request, body: RenameColumnRequest):
    """
    列名変更エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RenameColumnNameRequest
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
    result = rename_column(
        table_name=body.tableName,
        old_column_name=body.oldColumnName,
        new_column_name=body.newColumnName
    )
    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/add-lag-lead")
async def add_lag_lead_column_endpoint(request: Request, body: AddLagLeadColumnRequest):
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
    result = add_lag_lead_column(
        table_name=body.tableName,
        source_column=body.sourceColumn,
        new_column_name=body.newColumnName,
        periods=body.periods,
        group_columns=body.groupColumns
    )
    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

@router.post("/add-simulation")
async def add_simulation_column_endpoint(request: Request, body: AddSimulationColumnRequest):
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
    result = add_simulation_column(
        table_name=body.tableName,
        new_column_name=body.newColumnName,
        distribution_type=body.distributionType,
        distribution_params=body.distributionParams
    )
    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

@router.post("/calculate")
async def calculate_column_endpoint(request: Request, body: StatisticsCalculateColumnRequest):
    """カラム計算を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : StatisticsCalculateColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    result = calculate_column(
        table_name=body.tableName,
        new_column_name=body.newColumnName,
        calculation_expression=body.calculationExpression
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

@router.post("/duplicate")
async def duplicate_column_endpoint(request: Request, body: DataDuplicateColumnRequest):
    """カラムを複製するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DataDuplicateColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)
    # ビジネスロジックの実行
    result = duplicate_column(
        table_name=body.tableName,
        source_column_name=body.sourceColumnName,
        new_column_name=body.newColumnName
    )
    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

@router.post("/transform")
async def transform_column_endpoint(request: Request, body: TransformColumnRequest):
    """
    列の変換処理エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : OperationsTransformColumnRequest
        リクエストボディ
        - tableName: テーブル名
        - sourceColumnName: 変換元の列名
        - newColumnName: 新しい列名
        - transformMethod: 変換メソッド
        - logBase: 対数の底（オプション）
        - exponent: 指数（オプション）
        - rootIndex: 累乗根の次数（オプション）

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)
    # ビジネスロジックの実行
    result = transform_column(
        table_name=body.tableName,
        source_column_name=body.sourceColumnName,
        new_column_name=body.newColumnName,
        transform_method=body.transformMethod,
        log_base=body.logBase,
        exponent=body.exponent,
        root_index=body.rootIndex
    )
    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

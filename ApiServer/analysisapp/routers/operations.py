from fastapi import APIRouter, Request, status as http_status

from ..utils import create_success_response, create_log_api_request
from ..schemas import (
    InputCellDataRequest,
    FilterSingleConditionRequest
)
from ..services.input_cell_data import input_cell_data
from ..services.filter_single_condition import filter_single_condition

router = APIRouter(prefix="/operation", tags=["operation"])


@router.post("/input-cell-data")
async def input_cell_data_endpoint(request: Request, body: InputCellDataRequest):
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

    result = input_cell_data(
        body.tableName,
        body.columnName,
        body.rowIndex,
        body.newValue
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/filter-single-condition")
async def filter_single_condition_endpoint(request: Request, body: FilterSingleConditionRequest):
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

    result = filter_single_condition(
        new_table_name=body.newTableName,
        table_name=body.tableName,
        column_name=body.columnName,
        condition=body.condition,
        is_compare_column=body.isCompareColumn,
        compare_value=body.compareValue
    )

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )

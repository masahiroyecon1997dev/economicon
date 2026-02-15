"""テーブル操作関連のスキーマ定義"""

from typing import Annotated, Any, List

from pydantic import Field

from .common import BaseRequest
from .enums import FilterOperatorType, JoinType
from .types import (
    ColumnName,
    DistributionConfig,
    NewColumnName,
    NewTableName,
    TableName,
)


class CreateTableRequestBody(BaseRequest):
    """テーブル作成リクエスト"""

    table_name: NewTableName
    table_number_of_rows: int = Field(description="テーブルの行数", ge=1)
    column_names: List[NewColumnName] = Field(
        description="カラム名のリスト", min_length=1
    )


class RenameTableRequestBody(BaseRequest):
    """テーブル名変更リクエスト"""

    old_table_name: Annotated[TableName, Field(description="元のテーブル名")]
    new_table_name: Annotated[
        NewTableName, Field(description="新しいテーブル名")
    ]


class CreateSimulationDataTableRequestBody(BaseRequest):
    """シミュレーションデータテーブル作成リクエスト"""

    table_name: NewTableName
    table_number_of_rows: int = Field(description="テーブルの行数", ge=1)
    column_settings: List[DistributionConfig] = Field(
        description="カラム設定のリスト",
        min_length=1,
    )


class CreateJoinTableRequestBody(BaseRequest):
    """結合テーブル作成リクエスト"""

    join_table_name: Annotated[
        NewTableName, Field(description="結合後のテーブル名")
    ]
    left_table_name: Annotated[
        TableName, Field(description="左側のテーブル名")
    ]
    right_table_name: Annotated[
        TableName, Field(description="右側のテーブル名")
    ]
    left_key_column_names: List[ColumnName] = Field(
        description="左側の結合キーカラム名のリスト"
    )
    right_key_column_names: List[ColumnName] = Field(
        description="右側の結合キーカラム名のリスト"
    )
    join_type: JoinType = Field(
        default=JoinType.INNER,
        description="結合タイプ (inner, left, right, outer)",
    )


class CreateUnionTableRequestBody(BaseRequest):
    """ユニオンテーブル作成リクエスト"""

    union_table_name: Annotated[
        NewTableName, Field(description="ユニオン後のテーブル名")
    ]
    table_names: List[TableName] = Field(
        description="結合するテーブル名のリスト",
        min_length=2,
    )
    column_names: List[ColumnName] = Field(
        description="対象カラム名のリスト",
        min_length=1,
    )


class ClearTablesRequestBody(BaseRequest):
    """テーブルクリアリクエスト（パラメータなし）"""

    pass


class DuplicateTableRequestBody(BaseRequest):
    """テーブル複製リクエスト"""

    table_name: Annotated[TableName, Field(description="元のテーブル名")]
    new_table_name: Annotated[
        NewTableName, Field(description="新しいテーブル名")
    ]


class DeleteTableRequestBody(BaseRequest):
    """テーブル削除リクエスト"""

    table_name: Annotated[TableName, Field(description="削除するテーブル名")]


class FetchDataToJsonRequestBody(BaseRequest):
    """データJSON取得リクエスト"""

    table_name: TableName
    start_row: int = Field(description="開始行番号", ge=0)
    fetch_rows: int = Field(
        default=500, description="取得行数", ge=1, le=10000
    )


class FetchDataToArrowRequestBody(BaseRequest):
    """データArrow取得リクエスト"""

    table_name: TableName
    start_row: int = Field(description="開始行番号", ge=0)
    chunk_size: int = Field(
        default=500,
        description="チャンクサイズ（デフォルト500行）",
        ge=1,
        le=10000,
    )


class GetTableListRequestBody(BaseRequest):
    """テーブルリスト取得リクエスト（パラメータなし）"""

    pass


class InputCellDataRequestBody(BaseRequest):
    """セルデータ入力リクエスト"""

    table_name: TableName
    column_name: ColumnName
    row_index: int = Field(description="行インデックス", ge=0)
    new_value: Any = Field(description="新しい入力値")


class FilterSingleConditionRequestBody(BaseRequest):
    """単一条件フィルタリクエスト"""

    table_name: TableName
    new_table_name: NewTableName
    column_name: Annotated[
        ColumnName,
        Field(
            description="対象カラム名",
        ),
    ]
    condition: FilterOperatorType = Field(
        ..., description="条件", min_length=1, max_length=50
    )
    is_compare_column: str = Field(
        ...,
        alias="isCompareColumn",
        description="比較対象がカラムかどうか",
        min_length=1,
        max_length=10,
    )
    compare_value: Any = Field(..., alias="compareValue", description="比較値")

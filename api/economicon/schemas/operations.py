"""その他の操作関連のスキーマ定義"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InputCellDataRequest(BaseModel):
    """セルデータ入力リクエスト"""
    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255
    )
    column_name: str = Field(
        ...,
        alias="columnName",
        description="カラム名",
        min_length=1,
        max_length=255
    )
    row_index: int = Field(
        ...,
        alias="rowIndex",
        description="行インデックス",
        ge=0
    )
    new_value: Any = Field(
        ...,
        alias="newValue",
        description="新しい入力値"
    )

    model_config = ConfigDict(populate_by_name=True)


class FilterSingleConditionRequest(BaseModel):
    """単一条件フィルタリクエスト"""
    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255
    )
    new_table_name: str = Field(
        ...,
        alias="newTableName",
        description="新しいテーブル名",
        min_length=1,
        max_length=255
    )
    column_name: str = Field(
        ...,
        alias="columnName",
        description="対象カラム名",
        min_length=1,
        max_length=255
    )
    condition: str = Field(
        ...,
        description="条件",
        min_length=1,
        max_length=50
    )
    is_compare_column: str = Field(
        ...,
        alias="isCompareColumn",
        description="比較対象がカラムかどうか",
        min_length=1,
        max_length=10
    )
    compare_value: Any = Field(
        ...,
        alias="compareValue",
        description="比較値"
    )

    model_config = ConfigDict(populate_by_name=True)

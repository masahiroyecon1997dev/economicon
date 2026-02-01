"""テーブル操作関連のスキーマ定義"""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class CreateTableRequest(BaseModel):
    """テーブル作成リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    table_number_of_rows: int = Field(
        ..., alias="tableNumberOfRows", description="テーブルの行数", ge=1
    )
    column_names: List[str] = Field(
        ..., alias="columnNames", description="カラム名のリスト", min_length=1
    )

    model_config = ConfigDict(populate_by_name=True)


class RenameTableRequest(BaseModel):
    """テーブル名変更リクエスト"""

    old_table_name: str = Field(
        ...,
        alias="oldTableName",
        description="元のテーブル名",
        min_length=1,
        max_length=255,
    )
    new_table_name: str = Field(
        ...,
        alias="newTableName",
        description="新しいテーブル名",
        min_length=1,
        max_length=255,
    )

    model_config = ConfigDict(populate_by_name=True)


class CreateSimulationDataTableRequest(BaseModel):
    """シミュレーションデータテーブル作成リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    table_number_of_rows: int = Field(
        ..., alias="tableNumberOfRows", description="テーブルの行数", ge=1
    )
    column_settings: List[Dict[str, Any]] = Field(
        ...,
        alias="columnSettings",
        description="カラム設定のリスト",
        min_length=1,
    )

    model_config = ConfigDict(populate_by_name=True)


class CreateJoinTableRequest(BaseModel):
    """結合テーブル作成リクエスト"""

    join_table_name: str = Field(
        ...,
        alias="joinTableName",
        description="結合後のテーブル名",
        min_length=1,
        max_length=255,
    )
    left_table_name: str = Field(
        ...,
        alias="leftTableName",
        description="左側のテーブル名",
        min_length=1,
        max_length=255,
    )
    right_table_name: str = Field(
        ...,
        alias="rightTableName",
        description="右側のテーブル名",
        min_length=1,
        max_length=255,
    )
    left_key_column_names: List[str] = Field(
        ...,
        alias="leftKeyColumnNames",
        description="左側の結合キーカラム名のリスト",
        min_length=1,
    )
    right_key_column_names: List[str] = Field(
        ...,
        alias="rightKeyColumnNames",
        description="右側の結合キーカラム名のリスト",
        min_length=1,
    )
    join_type: str = Field(
        ...,
        alias="joinType",
        description="結合タイプ (inner, left, right, outer)",
        min_length=1,
        max_length=50,
    )

    model_config = ConfigDict(populate_by_name=True)


class CreateUnionTableRequest(BaseModel):
    """ユニオンテーブル作成リクエスト"""

    union_table_name: str = Field(
        ...,
        alias="unionTableName",
        description="ユニオン後のテーブル名",
        min_length=1,
        max_length=255,
    )
    table_names: List[str] = Field(
        ...,
        alias="tableNames",
        description="結合するテーブル名のリスト",
        min_length=1,
    )
    column_names: List[str] = Field(
        default_factory=list,
        alias="columnNames",
        description="対象カラム名のリスト",
    )

    model_config = ConfigDict(populate_by_name=True)


class ClearTablesRequest(BaseModel):
    """テーブルクリアリクエスト（パラメータなし）"""

    pass


class DuplicateTableRequest(BaseModel):
    """テーブル複製リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="元のテーブル名",
        min_length=1,
        max_length=255,
    )
    new_table_name: str = Field(
        ...,
        alias="newTableName",
        description="新しいテーブル名",
        min_length=1,
        max_length=255,
    )

    model_config = ConfigDict(populate_by_name=True)


class DeleteTableRequest(BaseModel):
    """テーブル削除リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )

    model_config = ConfigDict(populate_by_name=True)


class FetchDataToJsonRequest(BaseModel):
    """データJSON取得リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="対象テーブル名",
        min_length=1,
        max_length=255,
    )
    start_row: int = Field(
        ..., alias="startRow", description="開始行番号", ge=0
    )
    fetch_rows: int = Field(
        ..., alias="fetchRows", description="取得行数", ge=1
    )

    model_config = ConfigDict(populate_by_name=True)


class FetchDataToArrowRequest(BaseModel):
    """データArrow取得リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="対象テーブル名",
        min_length=1,
        max_length=255,
    )
    start_row: int = Field(
        ..., alias="startRow", description="開始行番号", ge=0
    )
    chunk_size: int = Field(
        default=500,
        alias="chunkSize",
        description="チャンクサイズ（デフォルト500行）",
        ge=1,
        le=10000,
    )

    model_config = ConfigDict(populate_by_name=True)


class GetTableListRequest(BaseModel):
    """テーブルリスト取得リクエスト（パラメータなし）"""

    pass

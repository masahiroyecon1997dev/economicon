"""カラム操作関連のスキーマ定義"""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AddColumnRequest(BaseModel):
    """カラム追加リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    new_column_name: str = Field(
        ...,
        alias="newColumnName",
        description="新しいカラム名",
        min_length=1,
        max_length=255,
    )
    add_position_column: str = Field(
        ...,
        alias="addPositionColumn",
        description="追加位置のカラム名",
        min_length=1,
        max_length=255,
    )
    model_config = ConfigDict(populate_by_name=True)


class AddColumnResult(BaseModel):
    """カラム追加レスポンス"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # Python名のままでも代入できるようにする
        from_attributes=True,  # self.table_name 等の属性から作成可能にする
    )

    table_name: str
    column_name: str


class DeleteColumnRequest(BaseModel):
    """カラム削除リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    column_name: str = Field(
        ...,
        alias="columnName",
        description="カラム名",
        min_length=1,
        max_length=255,
    )
    model_config = ConfigDict(populate_by_name=True)


class RenameColumnRequest(BaseModel):
    """カラム名変更リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    old_column_name: str = Field(
        ...,
        alias="oldColumnName",
        description="元のカラム名",
        min_length=1,
        max_length=255,
    )
    new_column_name: str = Field(
        ...,
        alias="newColumnName",
        description="新しいカラム名",
        min_length=1,
        max_length=255,
    )
    model_config = ConfigDict(populate_by_name=True)


class DuplicateColumnRequest(BaseModel):
    """カラム複製リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    source_column_name: str = Field(
        ...,
        alias="sourceColumnName",
        description="元のカラム名",
        min_length=1,
        max_length=255,
    )
    new_column_name: str = Field(
        ...,
        alias="newColumnName",
        description="新しいカラム名",
        min_length=1,
        max_length=255,
    )
    model_config = ConfigDict(populate_by_name=True)


class CalculateColumnRequest(BaseModel):
    """カラム計算リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    new_column_name: str = Field(
        ...,
        alias="newColumnName",
        description="新しいカラム名",
        min_length=1,
        max_length=255,
    )
    calculation_expression: str = Field(
        ..., alias="calculationExpression", description="計算式", min_length=1
    )
    model_config = ConfigDict(populate_by_name=True)


class AddDummyColumnRequest(BaseModel):
    """ダミー変数カラム追加リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    source_column_name: str = Field(
        ...,
        alias="sourceColumnName",
        description="元となるカラム名",
        min_length=1,
        max_length=255,
    )
    dummy_column_name: str = Field(
        ...,
        alias="dummyColumnName",
        description="ダミー変数カラム名",
        min_length=1,
        max_length=255,
    )
    target_value: str = Field(
        ..., alias="targetValue", description="1にする対象の値"
    )
    model_config = ConfigDict(populate_by_name=True)


class AddLagLeadColumnRequest(BaseModel):
    """ラグ・リードカラム追加リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    source_column: str = Field(
        ...,
        alias="sourceColumn",
        description="元となるカラム名",
        min_length=1,
        max_length=255,
    )
    new_column_name: str = Field(
        ...,
        alias="newColumnName",
        description="新しいカラム名",
        min_length=1,
        max_length=255,
    )
    periods: int = Field(..., alias="periods", description="ラグ・リード期間")
    group_columns: List[str] = Field(
        default_factory=list,
        alias="groupColumns",
        description="グループ化するカラムのリスト",
    )
    model_config = ConfigDict(populate_by_name=True)


class AddSimulationColumnRequest(BaseModel):
    """シミュレーションカラム追加リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    new_column_name: str = Field(
        ...,
        alias="newColumnName",
        description="新しいカラム名",
        min_length=1,
        max_length=255,
    )
    distribution_type: str = Field(
        ..., alias="distributionType", description="分布の種類", min_length=1
    )
    distribution_params: dict = Field(
        ..., alias="distributionParams", description="分布のパラメータ"
    )
    model_config = ConfigDict(populate_by_name=True)


class SortColumnsRequest(BaseModel):
    """カラムソートリクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    sort_columns: List[Dict[str, str]] = Field(
        ...,
        alias="sortColumns",
        description="ソート設定のリスト",
        min_length=1,
    )
    model_config = ConfigDict(populate_by_name=True)


class TransformColumnRequest(BaseModel):
    """カラム変換リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    source_column_name: str = Field(
        ...,
        alias="sourceColumnName",
        description="元となるカラム名",
        min_length=1,
        max_length=255,
    )
    new_column_name: str = Field(
        ...,
        alias="newColumnName",
        description="新しい列名",
        min_length=1,
        max_length=255,
    )
    transform_method: str = Field(
        ..., alias="transformMethod", description="変換メソッド", min_length=1
    )
    log_base: Optional[float] = Field(
        None, alias="logBase", description="対数の底（オプション）"
    )
    exponent: Optional[float] = Field(
        None, alias="exponent", description="指数（オプション）"
    )
    root_index: Optional[float] = Field(
        None, alias="rootIndex", description="累乗根の次数（オプション）"
    )
    model_config = ConfigDict(populate_by_name=True)


class GetColumnListRequest(BaseModel):
    """カラムリスト取得リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="対象テーブル名",
        min_length=1,
        max_length=255,
    )
    is_number_only: str = Field(
        default="false", alias="isNumberOnly", description="数値カラムのみ取得"
    )
    model_config = ConfigDict(populate_by_name=True)

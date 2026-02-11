"""カラム操作関連のスキーマ定義"""

from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import BaseRequest
from .schemas import SortInstruction
from .types import ColumnName, NewColumnName, TableName


class AddColumnRequest(BaseRequest):
    """カラム追加リクエスト"""

    table_name: TableName
    new_column_name: NewColumnName
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名",
        ),
    ]


class AddColumnResult(BaseModel):
    """カラム追加レスポンス"""

    table_name: str
    column_name: str


class DeleteColumnRequest(BaseRequest):
    """カラム削除リクエスト"""

    table_name: TableName
    column_name: Annotated[ColumnName, Field(description="削除するカラム名")]


class RenameColumnRequest(BaseRequest):
    """カラム名変更リクエスト"""

    table_name: TableName
    old_column_name: Annotated[
        ColumnName, Field(description="変更前のカラム名")
    ]
    new_column_name: Annotated[
        NewColumnName, Field(description="新しいカラム名")
    ]


class DuplicateColumnRequest(BaseRequest):
    """カラム複製リクエスト"""

    table_name: TableName
    source_column_name: Annotated[
        ColumnName, Field(description="元となるカラム名")
    ]
    new_column_name: Annotated[
        NewColumnName, Field(description="新しいカラム名")
    ]


class CalculateColumnRequest(BaseRequest):
    """カラム計算リクエスト"""

    table_name: TableName
    new_column_name: NewColumnName
    calculation_expression: str = Field(description="計算式", min_length=1)


class AddDummyColumnRequest(BaseRequest):
    """ダミー変数カラム追加リクエスト"""

    table_name: TableName
    source_column_name: Annotated[
        ColumnName, Field(description="元となるカラム名")
    ]
    dummy_column_name: Annotated[
        NewColumnName, Field(description="新しいカラム名")
    ]
    target_value: str = Field(description="1にする対象の値")


class AddLagLeadColumnRequest(BaseRequest):
    """ラグ・リードカラム追加リクエスト"""

    table_name: TableName
    source_column: Annotated[
        ColumnName,
        Field(
            description="元となるカラム名",
        ),
    ]
    new_column_name: NewColumnName
    periods: int = Field(alias="periods", description="ラグ・リード期間")
    group_columns: List[str] = Field(
        default_factory=list,
        description="グループ化するカラムのリスト",
    )
    model_config = ConfigDict(populate_by_name=True)


class AddSimulationColumnRequest(BaseRequest):
    """シミュレーションカラム追加リクエスト"""

    table_name: TableName
    new_column_name: NewColumnName
    distribution_type: str = Field(
        ..., alias="distributionType", description="分布の種類", min_length=1
    )
    distribution_params: dict = Field(
        ..., alias="distributionParams", description="分布のパラメータ"
    )
    model_config = ConfigDict(populate_by_name=True)


class SortColumnsRequest(BaseRequest):
    """カラムソートリクエスト"""

    table_name: TableName
    sort_columns: List[SortInstruction] = Field(
        description="ソート設定のリスト",
        min_length=1,
    )
    model_config = ConfigDict(populate_by_name=True)


class TransformColumnRequest(BaseRequest):
    """カラム変換リクエスト"""

    table_name: TableName
    source_column_name: Annotated[
        ColumnName,
        Field(
            description="元となるカラム名",
        ),
    ]
    new_column_name: NewColumnName
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


class GetColumnListRequest(BaseRequest):
    """カラムリスト取得リクエスト"""

    table_name: TableName
    is_number_only: bool = Field(
        False, description="数値カラムのみ取得するかどうか"
    )

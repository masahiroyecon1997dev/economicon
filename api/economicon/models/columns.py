"""カラム操作関連のスキーマ定義"""

from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

from .common import BaseRequest
from .entities import SimulationColumnConfig, SortInstruction
from .types import (
    ColumnName,
    FilePath,
    NewColumnName,
    TableName,
    TransformMethodConfig,
)


class AddColumnRequestBody(BaseRequest):
    """カラム追加リクエスト"""

    table_name: TableName
    new_column_name: NewColumnName
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名",
        ),
    ]
    csv_file_path: Optional[FilePath] = None
    csv_has_header: Annotated[
        bool,
        Field(
            alias="csvHasHeader",
            description="CSVファイルにヘッダ行があるか（True:ヘッダ行をスキップして2行目から読み込む、False:1行目から読み込む）",
        ),
    ] = True
    csv_strict_row_count: Annotated[
        bool,
        Field(
            alias="csvStrictRowCount",
            description="行数の厳密チェック（True:行数不一致でエラー、False:超過分を切り捨て・不足分はNoneで埋める）",
        ),
    ] = True
    separator: Annotated[
        str,
        Field(
            description="CSV区切り文字",
            min_length=1,
            max_length=10,
        ),
    ] = ","


class AddColumnResult(BaseModel):
    """カラム追加レスポンス"""

    table_name: TableName
    column_name: ColumnName


class DeleteColumnRequestBody(BaseRequest):
    """カラム削除リクエスト"""

    table_name: TableName
    column_name: Annotated[ColumnName, Field(description="削除するカラム名")]


class DeleteColumnResult(BaseModel):
    """カラム削除レスポンス"""

    table_name: TableName
    column_name: ColumnName


class RenameColumnRequestBody(BaseRequest):
    """カラム名変更リクエスト"""

    table_name: TableName
    old_column_name: Annotated[
        ColumnName, Field(description="変更前のカラム名")
    ]
    new_column_name: Annotated[
        NewColumnName, Field(description="新しいカラム名")
    ]


class DuplicateColumnRequestBody(BaseRequest):
    """カラム複製リクエスト"""

    table_name: TableName
    source_column_name: Annotated[
        ColumnName, Field(description="元となるカラム名")
    ]
    new_column_name: Annotated[
        NewColumnName, Field(description="新しいカラム名")
    ]


class CalculateColumnRequestBody(BaseRequest):
    """カラム計算リクエスト"""

    table_name: TableName
    new_column_name: NewColumnName
    calculation_expression: str = Field(description="計算式", min_length=1)


class AddDummyColumnRequestBody(BaseRequest):
    """ダミー変数カラム追加リクエスト"""

    table_name: TableName
    source_column_name: Annotated[
        ColumnName, Field(description="元となるカラム名")
    ]
    dummy_column_name: Annotated[
        NewColumnName, Field(description="新しいカラム名")
    ]
    target_value: str = Field(description="1にする対象の値", min_length=1)


class AddLagLeadColumnRequestBody(BaseRequest):
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
    group_columns: List[ColumnName] = Field(
        default_factory=list,
        description="グループ化するカラムのリスト",
    )


class AddSimulationColumnRequestBody(BaseRequest):
    """シミュレーションカラム追加リクエスト"""

    table_name: TableName
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名",
        ),
    ]
    simulation_column: SimulationColumnConfig


class SortColumnsRequestBody(BaseRequest):
    """カラムソートリクエスト"""

    table_name: TableName
    sort_columns: List[SortInstruction] = Field(
        description="ソート設定のリスト",
        min_length=1,
    )


class TransformColumnRequestBody(BaseRequest):
    """カラム変換リクエスト"""

    table_name: TableName
    source_column_name: Annotated[
        ColumnName,
        Field(
            description="元となるカラム名",
        ),
    ]
    new_column_name: NewColumnName
    transform_method: TransformMethodConfig


class GetColumnListRequestBody(BaseRequest):
    """カラムリスト取得リクエスト"""

    table_name: TableName
    is_number_only: bool = Field(
        False, description="数値カラムのみ取得するかどうか"
    )

"""カラム操作関連のスキーマ定義"""

from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, StringConstraints

from .common import BaseRequest
from .entities import SimulationColumnConfig, SortInstruction
from .types import (
    ColumnName,
    FilePath,
    NewColumnName,
    Separator,
    TableName,
    TransformMethodConfig,
)


class AddColumnRequestBody(BaseRequest):
    """カラム追加リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="列を追加するテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    new_column_name: Annotated[
        NewColumnName,
        Field(
            description="追加する新しいカラム名。既存のカラム名と重複しない名前を指定してください。"
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名。指定したカラムの右隣に新しいカラムが追加されます。既存のカラム名から指定してください。",
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
        Separator,
        Field(
            description="CSV区切り文字。カンマかタブ、もしくは1から10文字の任意の文字列から選択してください。",
            min_length=1,
            max_length=10,
        ),
    ] = ","


class AddColumnResult(BaseModel):
    """カラム追加レスポンス"""

    table_name: Annotated[
        TableName,
        Field(description="列を追加したテーブル名"),
    ]
    column_name: Annotated[
        ColumnName,
        Field(description="追加したカラム名"),
    ]


class DeleteColumnRequestBody(BaseRequest):
    """カラム削除リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="列を削除するテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    column_name: Annotated[
        ColumnName,
        Field(
            description="削除するカラム名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]


class DeleteColumnResult(BaseModel):
    """カラム削除レスポンス"""

    table_name: Annotated[
        TableName,
        Field(
            description="列を削除したテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    column_name: Annotated[
        ColumnName,
        Field(
            description="削除したカラム名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]


class RenameColumnRequestBody(BaseRequest):
    """カラム名変更リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="カラム名を変更するテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    old_column_name: Annotated[
        ColumnName,
        Field(
            description="変更前のカラム名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    new_column_name: Annotated[
        NewColumnName,
        Field(
            description="新しいカラム名。既存のカラム名と重複しない名前を指定してください。",
        ),
    ]


class DuplicateColumnRequestBody(BaseRequest):
    """カラム複製リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="操作対象のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    source_column_name: Annotated[
        ColumnName,
        Field(
            description="元となるカラム名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    new_column_name: Annotated[
        NewColumnName,
        Field(
            description="新しいカラム名。既存のカラム名と重複しない名前を指定してください。"
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名。指定したカラムの右隣に新しいカラムが追加されます。既存のカラム名から指定してください。",
        ),
    ]


class CalculateColumnRequestBody(BaseRequest):
    """カラム計算リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="操作対象のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    new_column_name: Annotated[
        NewColumnName,
        Field(
            description="新しいカラム名。既存のカラム名と重複しない名前を指定してください。"
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名。指定したカラムの右隣に新しいカラムが追加されます。既存のカラム名から指定してください。",
        ),
    ]
    calculation_expression: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
        Field(
            title="Calculation Expression",
            examples=['pl.col("price") * pl.col("quantity")'],
            description='計算式。数値カラム名をpl.col("price")の形式で指定し、四則演算や関数を組み合わせて計算式を定義してください。例: ({population} / {area}) * 1000',
        ),
    ]


class AddDummyColumnRequestBody(BaseRequest):
    """ダミー変数カラム追加リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="操作対象のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    source_column_name: Annotated[
        ColumnName,
        Field(
            description="ダミー変数を作成する元となるカラム名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    dummy_column_name: Annotated[
        NewColumnName,
        Field(
            description="新しいカラム名。既存のカラム名と重複しない名前を指定してください。"
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名。指定したカラムの右隣に新しいカラムが追加されます。既存のカラム名から指定してください。",
        ),
    ]
    target_value: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
        Field(
            title="Target Value",
            examples=["Tokyo", "東京"],
            description="列に存在する1にする対象の値。例えば、元の列が都市名で、東京を1、それ以外を0にしたい場合は、'Tokyo'や'東京'を指定してください。",
        ),
    ]


class AddLagLeadColumnRequestBody(BaseRequest):
    """ラグ・リードカラム追加リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="操作対象のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    source_column: Annotated[
        ColumnName,
        Field(
            description="ラグ・リードの元となるカラム名。ワークスペースに存在するテーブルの中から指定してください。",
        ),
    ]
    new_column_name: Annotated[
        NewColumnName,
        Field(
            description="新しいカラム名。既存のカラム名と重複しない名前を指定してください。"
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名。指定したカラムの右隣に新しいカラムが追加されます。既存のカラム名から指定してください。",
        ),
    ]
    periods: Annotated[
        int,
        Field(
            title="Periods",
            ge=1,
            examples=[1, 2, 3],
            description="ラグ・リードの期間。例えば、1を指定すると1行前（ラグ）または1行後（リード）の値が新しいカラムに入ります。2を指定すると2行前後の値が入ります。",
        ),
    ]
    group_columns: Annotated[
        List[ColumnName],
        Field(
            title="Group Columns",
            examples=[["city"], ["都市"]],
            default_factory=list,
            description="ラグ・リードのグループ化に使用するカラムのリスト。指定したカラムの組み合わせごとにラグ・リードが計算されます。例えば、都市ごとにラグ・リードを計算したい場合は、['city']や['都市']を指定してください。複数カラムを指定することもできます。既存カラム名から指定してください。",
        ),
    ]


class AddSimulationColumnRequestBody(BaseRequest):
    """シミュレーションカラム追加リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="操作対象のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    simulation_column: Annotated[
        SimulationColumnConfig,
        Field(
            title="Simulation Column Config",
            description="シミュレーションカラムの設定。",
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名。指定したカラムの右隣に新しいカラムが追加されます。既存のカラム名から指定してください。",
        ),
    ]


class SortColumnsRequestBody(BaseRequest):
    """カラムソートリクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="操作対象のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    sort_columns: Annotated[
        List[SortInstruction],
        Field(
            title="Sort Instructions",
            description="ソート設定のリスト。ソートするカラム名と昇順・降順の指定を組み合わせて、複数カラムでのソートも可能です。既存カラム名から指定してください。",
            min_length=1,
        ),
    ]


class TransformColumnRequestBody(BaseRequest):
    """カラム変換リクエスト"""

    table_name: TableName
    source_column_name: Annotated[
        ColumnName,
        Field(
            description="元となるカラム名",
        ),
    ]
    new_column_name: Annotated[
        NewColumnName,
        Field(
            description="新しいカラム名。既存のカラム名と重複しない名前を指定してください。"
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description="追加位置のカラム名。指定したカラムの右隣に新しいカラムが追加されます。既存のカラム名から指定してください。",
        ),
    ]
    transform_method: TransformMethodConfig


class GetColumnListRequestBody(BaseRequest):
    """カラムリスト取得リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="操作対象のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    is_number_only: Annotated[
        bool,
        Field(
            False,
            title="Is Number Only",
            description="数値カラムのみ取得するかどうか。Trueを指定すると、数値カラムのみが返されます。Falseを指定すると、全てのカラムが返されます。",
        ),
    ]

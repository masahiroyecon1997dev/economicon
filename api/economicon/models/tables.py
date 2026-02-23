"""テーブル操作関連のスキーマ定義"""

from typing import Annotated, Any, Self

from pydantic import BeforeValidator, Field, model_validator
from pydantic_core import PydanticCustomError

from .common import BaseRequest, BaseResult
from .entities import SimulationColumnConfig
from .enums import FilterOperatorType, JoinType
from .types import (
    ColumnName,
    CsvEncoding,
    ExcelSheetName,
    FilePath,
    NewColumnName,
    NewTableName,
    Separator,
    TableName,
)

# ---------------------------------------------------------------------------
# バリデーション関数
# ---------------------------------------------------------------------------


def _coerce_join_type(v: Any) -> JoinType:
    """JSON文字列をJoinTypeに変換するBeforeValidator"""
    if isinstance(v, JoinType):
        return v
    if isinstance(v, str):
        try:
            return JoinType(v)
        except ValueError:
            valid = ", ".join(e.value for e in JoinType)
            raise PydanticCustomError(
                "literal_error",
                "joinTypeは次のいずれかである必要があります: {expected}",
                {"expected": valid},
            ) from None
    return v


def _coerce_filter_operator_type(v: Any) -> FilterOperatorType:
    """JSON文字列をFilterOperatorTypeに変換するBeforeValidator"""
    if isinstance(v, FilterOperatorType):
        return v
    if isinstance(v, str):
        try:
            return FilterOperatorType(v)
        except ValueError:
            valid = ", ".join(e.value for e in FilterOperatorType)
            raise PydanticCustomError(
                "literal_error",
                "conditionは次のいずれかである必要があります: {expected}",
                {"expected": valid},
            ) from None
    return v


# ---------------------------------------------------------------------------
# リクエストボディ
# ---------------------------------------------------------------------------


class CreateTableRequestBody(BaseRequest):
    """テーブル作成リクエスト"""

    table_name: Annotated[
        NewTableName,
        Field(
            title="Table Name",
            description="作成するテーブルの名前。ワークスペース内に存在しない名前を指定してください。",
        ),
    ]
    row_count: Annotated[
        int | None,
        Field(
            title="Row Count",
            description=(
                "テーブルの行数。"
                "file_path が指定されている場合は省略可能"
                "（None の場合はファイルの行数を使用）。"
                "file_path が省略されている場合は必須（1以上の整数）。"
            ),
            ge=1,
        ),
    ] = None
    column_names: Annotated[
        list[NewColumnName],
        Field(
            title="Column Names",
            description="テーブルに作成するカラム名のリスト",
            min_length=1,
        ),
    ]
    file_path: Annotated[
        FilePath | None,
        Field(
            title="File Path",
            description=(
                "読み込むファイルのパス（CSV / Excel / Parquet）。"
                "省略時はすべての値が None の空テーブルを作成します。"
            ),
        ),
    ] = None
    csv_has_header: Annotated[
        bool,
        Field(
            title="CSV Has Header",
            description=(
                "CSV ファイルにヘッダ行があるか。"
                "True: 1 行目をヘッダとして読み飛ばし、"
                "2 行目からをデータとする。"
                "False: 1 行目からデータとして読み込む。"
                "file_path が CSV の場合のみ有効。"
            ),
        ),
    ] = True
    csv_separator: Annotated[
        Separator,
        Field(
            title="CSV Separator",
            description="CSV の区切り文字。file_path が CSV の場合のみ有効。",
            min_length=1,
            max_length=10,
        ),
    ] = ","
    csv_encoding: Annotated[
        CsvEncoding,
        Field(
            title="CSV Encoding",
            description=(
                "CSV のエンコーディング。file_path が CSV の場合のみ有効。"
            ),
        ),
    ] = "utf8"
    excel_sheet_name: Annotated[
        ExcelSheetName | None,
        Field(
            title="Excel Sheet Name",
            description=(
                "読み込むシート名。file_path が Excel の場合のみ有効。"
                "省略時は先頭シートを読み込みます。"
            ),
        ),
    ] = None

    @model_validator(mode="after")
    def require_rows_when_no_file(self) -> Self:
        """file_path が None のとき row_count は必須"""
        if self.file_path is None and self.row_count is None:
            raise ValueError(
                "row_count is required when file_path is not specified"
            )
        return self


class RenameTableRequestBody(BaseRequest):
    """テーブル名変更リクエスト"""

    old_table_name: Annotated[
        TableName,
        Field(title="Old Table Name", description="変更前のテーブル名"),
    ]
    new_table_name: Annotated[
        NewTableName,
        Field(title="New Table Name", description="変更後の新しいテーブル名"),
    ]


class CreateSimulationDataTableRequestBody(BaseRequest):
    """シミュレーションデータテーブル作成リクエスト"""

    table_name: Annotated[
        NewTableName,
        Field(
            description="作成するシミュレーションデータテーブルの名前。ワークスペース内に存在しない名前を指定してください。",
        ),
    ]
    row_count: Annotated[
        int,
        Field(
            title="Row Count",
            description="生成するテーブルの行数",
            ge=1,
        ),
    ]
    simulation_columns: Annotated[
        list[SimulationColumnConfig],
        Field(
            title="Simulation Columns",
            description="シミュレーションカラムの設定リスト",
            min_length=1,
        ),
    ]


class CreateJoinTableRequestBody(BaseRequest):
    """結合テーブル作成リクエスト"""

    join_table_name: Annotated[
        NewTableName,
        Field(
            title="Join Table Name",
            description="結合後に作成される新しいテーブル名。ワークスペース内に存在しない名前を指定してください。",
        ),
    ]
    left_table_name: Annotated[
        TableName,
        Field(
            title="Left Table Name",
            description="結合の左側テーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    right_table_name: Annotated[
        TableName,
        Field(
            title="Right Table Name",
            description="結合の右側テーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    left_key_column_names: Annotated[
        list[ColumnName],
        Field(
            title="Left Key Column Names",
            description="左側テーブルの結合キーカラム名のリスト",
            min_length=1,
        ),
    ]
    right_key_column_names: Annotated[
        list[ColumnName],
        Field(
            title="Right Key Column Names",
            description="右側テーブルの結合キーカラム名のリスト",
            min_length=1,
        ),
    ]
    join_type: Annotated[
        JoinType,
        BeforeValidator(_coerce_join_type),
        Field(
            default=JoinType.INNER,
            title="Join Type",
            description="結合タイプ"
            "（inner: 内部結合、left: 左外部結合、"
            "right: 右外部結合、full: 完全外部結合）",
        ),
    ]


class CreateUnionTableRequestBody(BaseRequest):
    """ユニオンテーブル作成リクエスト"""

    union_table_name: Annotated[
        NewTableName,
        Field(
            title="Union Table Name",
            description="ユニオン後に作成される新しいテーブル名",
        ),
    ]
    table_names: Annotated[
        list[TableName],
        Field(
            title="Table Names",
            description="ユニオンするテーブル名のリスト（2テーブル以上）。ワークスペース内に存在するテーブル名を指定してください。",
            min_length=2,
        ),
    ]
    column_names: Annotated[
        list[ColumnName],
        Field(
            title="Column Names",
            description="ユニオンの対象とするカラム名のリスト。指定されたテーブルすべてに存在するカラム名を指定してください。",
            min_length=1,
        ),
    ]


class ClearTablesRequestBody(BaseRequest):
    """テーブルクリアリクエスト（パラメータなし）"""

    pass


class DuplicateTableRequestBody(BaseRequest):
    """テーブル複製リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="複製元のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    new_table_name: Annotated[
        NewTableName,
        Field(
            description="複製後の新しいテーブル名。ワークスペースに存在しない名前を指定してください。"
        ),
    ]


class DeleteTableRequestBody(BaseRequest):
    """テーブル削除リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="削除するテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]


class FetchDataToJsonRequestBody(BaseRequest):
    """データJSON取得リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="データを取得するテーブル名。ワークスペースに存在するテーブルの中から指定してください。",
        ),
    ]
    start_row: Annotated[
        int,
        Field(
            title="Start Row",
            description="取得を開始する行番号（0始まり）",
            ge=0,
        ),
    ]
    fetch_rows: Annotated[
        int,
        Field(
            default=500,
            title="Fetch Rows",
            description="取得する行数（1〜10000、デフォルト500）",
            ge=1,
            le=10000,
        ),
    ]


class FetchDataToArrowRequestBody(BaseRequest):
    """データArrow取得リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="データを取得するテーブル名。ワークスペースに存在するテーブルの中から指定してください。",
        ),
    ]
    start_row: Annotated[
        int,
        Field(
            title="Start Row",
            description="取得を開始する行番号（0始まり）",
            ge=0,
        ),
    ]
    chunk_size: Annotated[
        int,
        Field(
            default=500,
            title="Chunk Size",
            description="1リクエストで取得する行数（1〜10000、デフォルト500）",
            ge=1,
            le=10000,
        ),
    ]


class GetTableListRequestBody(BaseRequest):
    """テーブルリスト取得リクエスト（パラメータなし）"""

    pass


class InputCellDataRequestBody(BaseRequest):
    """セルデータ入力リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="セルデータを入力するテーブル名。ワークスペースに存在するテーブルの中から指定してください。",
        ),
    ]
    column_name: Annotated[
        ColumnName,
        Field(
            description="セルデータを入力するカラム名。ワークスペースに存在するテーブルの中から指定してください。",
        ),
    ]
    row_index: Annotated[
        int,
        Field(
            title="Row Index",
            description="更新するセルの行インデックス（0始まり）",
            ge=0,
        ),
    ]
    new_value: Annotated[
        Any,
        Field(
            title="New Value",
            description="セルに入力する新しい値。カラムのデータ型に合わせた値を指定してください。",
        ),
    ]


class FilterSingleConditionRequestBody(BaseRequest):
    """単一条件フィルタリクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="フィルタ条件を適用するテーブル名。ワークスペースに存在するテーブルの中から指定してください。",
        ),
    ]
    new_table_name: Annotated[
        NewTableName,
        Field(
            description="フィルタ結果を格納する新しいテーブル名。ワークスペースに存在しない名前を指定してください。",
        ),
    ]
    column_name: Annotated[
        ColumnName,
        Field(
            description="フィルタ条件を適用するカラム名。ワークスペースに存在するテーブルの中から指定してください。",
        ),
    ]
    condition: Annotated[
        FilterOperatorType,
        BeforeValidator(_coerce_filter_operator_type),
        Field(
            title="Condition",
            description="フィルタ条件の演算子"
            "（equals, notEquals, greaterThan, lessThan 等）",
        ),
    ]
    is_compare_column: Annotated[
        str,
        Field(
            title="Is Compare Column",
            description="比較対象がカラムかどうか。"
            '"true": compareValue をカラム名として解釈、'
            '"false": 定数値として解釈。',
            min_length=1,
            max_length=10,
        ),
    ]
    compare_value: Annotated[
        Any,
        Field(
            title="Compare Value",
            description="比較する値またはカラム名。"
            'isCompareColumn が "true" の場合はカラム名を指定。',
        ),
    ]


# ---------------------------------------------------------------------------
# レスポンス（Result）
# ---------------------------------------------------------------------------


class TableNameResult(BaseResult):
    """テーブル名のみを返す共通レスポンス基底"""

    table_name: str = Field(
        title="Table Name",
        description="操作対象または生成されたテーブル名",
    )


class CreateTableResult(TableNameResult):
    """テーブル作成レスポンス"""


class CreateJoinTableResult(TableNameResult):
    """結合テーブル作成レスポンス"""


class CreateUnionTableResult(TableNameResult):
    """ユニオンテーブル作成レスポンス"""


class CreateSimulationDataTableResult(TableNameResult):
    """シミュレーションデータテーブル作成レスポンス"""


class DeleteTableResult(TableNameResult):
    """テーブル削除レスポンス"""


class DuplicateTableResult(TableNameResult):
    """テーブル複製レスポンス"""


class RenameTableResult(TableNameResult):
    """テーブル名変更レスポンス"""


class GetTableListResult(BaseResult):
    """テーブルリスト取得レスポンス"""

    table_name_list: list[str] = Field(
        title="Table Name List",
        description="ワークスペースに存在するテーブル名のリスト",
    )


class ClearTablesResult(BaseResult):
    """全テーブルクリアレスポンス（データなし）"""


class FetchDataToJsonResult(BaseResult):
    """テーブルデータ JSON 形式取得レスポンス"""

    table_name: str = Field(
        title="Table Name",
        description="データを取得したテーブル名",
    )
    data: str = Field(
        title="Data",
        description="JSON 文字列形式のテーブルデータ",
    )
    total_rows: int = Field(
        title="Total Rows",
        description="テーブル全体の行数",
    )
    start_row: int = Field(
        title="Start Row",
        description="取得開始行番号",
    )
    end_row: int = Field(
        title="End Row",
        description="取得終了行番号",
    )


class InputCellDataResult(TableNameResult):
    """セルデータ入力レスポンス"""


class FilterSingleConditionResult(TableNameResult):
    """単一条件フィルタレスポンス"""

"""カラム操作関連のスキーマ定義"""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import BaseRequest, BaseResult
from economicon.schemas.enums import (
    DistributionType,
    DummyMode,
    NullStrategy,
)
from economicon.schemas.shared_entities import (
    SimulationColumnConfig,
    SortInstruction,
)
from economicon.schemas.types import (
    ColumnName,
    NewColumnName,
    TableName,
    TransformMethodConfig,
)

# ---------------------------------------------------------------------------
# カラム削除
# ---------------------------------------------------------------------------


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


class DeleteColumnResult(BaseResult):
    """カラム削除レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="カラムを削除したテーブル名",
        ),
    ]


# ---------------------------------------------------------------------------
# カラム名変更
# ---------------------------------------------------------------------------


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

    @model_validator(mode="after")
    def _validate_names_differ(
        self,
    ) -> RenameColumnRequestBody:
        if self.old_column_name == self.new_column_name:
            raise ValueError(
                _("newColumnName must differ from oldColumnName.")
            )
        return self


class RenameColumnResult(BaseResult):
    """カラム名変更レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="カラム名を変更したテーブル名",
        ),
    ]
    column_name: Annotated[
        str,
        Field(
            title="Column Name",
            description="変更後のカラム名",
        ),
    ]


# ---------------------------------------------------------------------------
# カラム計算
# ---------------------------------------------------------------------------


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
            description=(
                "計算式。数値カラム名をpl.col('price')の形式で指定し、"
                "四則演算や関数を組み合わせて計算式を定義してください。"
                "例: ({population} / {area}) * 1000')"
            ),
        ),
    ]

    @field_validator("calculation_expression", mode="after")
    @classmethod
    def _validate_expression_syntax(cls, v: str) -> str:
        """計算式の構文を Pydantic バリデーション段階で検証する。

        AST レベルで構文エラー・未サポート操作を検出し 422 として早期に返す。
        循環インポート回避のためローカル import を使用する。
        """
        # 循環インポート回避のため、ここでローカルインポートする
        from economicon.utils.algorithms import (  # noqa: PLC0415
            validate_formula_syntax,
        )

        validate_formula_syntax(v)
        return v


class CalculateColumnResult(BaseResult):
    """カラム計算レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="計算カラムを追加したテーブル名",
        ),
    ]
    column_name: Annotated[
        str,
        Field(
            title="Column Name",
            description="追加した計算カラム名",
        ),
    ]


# ---------------------------------------------------------------------------
# ダミー変数カラム追加
# ---------------------------------------------------------------------------


class AddDummyColumnRequestBody(BaseRequest):
    """ダミー変数カラム追加リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description=(
                "操作対象のテーブル名。"
                "ワークスペースに存在するテーブルの中から指定してください。"
            )
        ),
    ]
    source_column_name: Annotated[
        ColumnName,
        Field(
            description=(
                "ダミー変数を作成する元となるカラム名。"
                "ワークスペースに存在するテーブルの中から指定してください。"
            )
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description=(
                "追加位置のカラム名。指定したカラムの右隣に"
                "新しいカラムが追加されます。"
                "既存のカラム名から指定してください。"
            ),
        ),
    ]
    mode: Annotated[
        DummyMode,
        Field(
            strict=False,
            title="Mode",
            description=(
                "ダミー化モード。"
                "'single': 特定の1値をダミー化する。"
                "'all_except_base': 基準値を除いた全カテゴリを"
                "一括ダミー化する。"
            ),
        ),
    ] = DummyMode.SINGLE
    dummy_column_name: Annotated[
        NewColumnName | None,
        Field(
            default=None,
            description=(
                "新しいカラム名。single モード時は必須。"
                "all_except_base モードでは無視され、"
                "{source}_{value} 形式で自動生成されます。"
            ),
        ),
    ]
    target_value: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=1),
        Field(
            default=None,
            title="Target Value",
            examples=["Tokyo", "東京"],
            description=(
                "single モード時のみ必須。列に存在する1にする対象の値。"
            ),
        ),
    ]
    drop_base_value: Annotated[
        str | None,
        Field(
            default=None,
            title="Drop Base Value",
            examples=["Tokyo", "auto_most_frequent"],
            description=(
                "all_except_base モード時のみ必須。"
                "ダミー化から除外する基準カテゴリ値。"
                "'auto_most_frequent' を指定すると"
                "最頻値を自動選択します。"
            ),
        ),
    ]
    null_strategy: Annotated[
        NullStrategy,
        Field(
            strict=False,
            title="Null Strategy",
            description=(
                "null値（空文字・空白を含む）の扱い。"
                "'exclude': null を無視してダミーを生成しない。"
                "'as_category': null を '__null__' カテゴリとして扱う。"
                "'error': null が存在する場合エラーを返す。"
            ),
        ),
    ] = NullStrategy.EXCLUDE

    @model_validator(mode="after")
    def _validate_mode_fields(
        self,
    ) -> AddDummyColumnRequestBody:
        if self.mode == DummyMode.SINGLE:
            if self.target_value is None:
                raise ValueError(
                    "targetValue は mode='single' のとき必須です。"
                )
            if self.dummy_column_name is None:
                raise ValueError(
                    "dummyColumnName は mode='single' のとき必須です。"
                )
        elif self.mode == DummyMode.ALL_EXCEPT_BASE:
            if self.drop_base_value is None:
                raise ValueError(
                    "dropBaseValue は mode='all_except_base' のとき必須です。"
                )
        return self


class AddDummyColumnResult(BaseResult):
    """ダミー変数カラム追加レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="ダミーカラムを追加したテーブル名",
        ),
    ]
    added_column_names: Annotated[
        list[str],
        Field(
            title="Added Column Names",
            description="追加したダミーカラム名のリスト",
        ),
    ]


# ---------------------------------------------------------------------------
# ラグ・リードカラム追加
# ---------------------------------------------------------------------------


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
            examples=[-1, -2, 1, 2],
            description=(
                "ラグ・リードの期間。負の値（-1, -2...）はラグ変数、"
                "正の値（1, 2...）はリード変数を作成します。"
                "例えば、-1を指定すると1行前の値（ラグ1）、1を指定すると1行後の値（リード1）が新しいカラムに入ります。"
            ),
        ),
    ]
    group_columns: Annotated[
        list[ColumnName],
        Field(
            title="Group Columns",
            examples=[["city"], ["都市"]],
            default_factory=list,
            description="ラグ・リードのグループ化に使用するカラムのリスト。指定したカラムの組み合わせごとにラグ・リードが計算されます。例えば、都市ごとにラグ・リードを計算したい場合は、['city']や['都市']を指定してください。複数カラムを指定することもできます。既存カラム名から指定してください。",
        ),
    ]


class AddLagLeadColumnResult(BaseResult):
    """ラグ・リードカラム追加レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="ラグ・リードカラムを追加したテーブル名",
        ),
    ]
    column_name: Annotated[
        str,
        Field(
            title="Column Name",
            description="追加したラグ・リードカラム名",
        ),
    ]


# ---------------------------------------------------------------------------
# シミュレーションカラム追加
# ---------------------------------------------------------------------------


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
    random_seed: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            le=100_000_000,
            title="Random Seed",
            description=(
                "乱数シード値（0以上1億以下の整数）。"
                "同じシードを指定すると同じ結果が再現されます。"
                "None の場合は毎回異なる結果になります。"
            ),
        ),
    ]


class AddSimulationColumnResult(BaseResult):
    """シミュレーションカラム追加レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="シミュレーションカラムを追加したテーブル名",
        ),
    ]
    column_name: Annotated[
        str,
        Field(
            title="Column Name",
            description="追加したシミュレーションカラム名",
        ),
    ]
    distribution_type: DistributionType = Field(
        title="Distribution Type",
        description="使用した分布タイプ",
    )


# ---------------------------------------------------------------------------
# カラムソート
# ---------------------------------------------------------------------------


class SortColumnsRequestBody(BaseRequest):
    """カラムソートリクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description="操作対象のテーブル名。ワークスペースに存在するテーブルの中から指定してください。"
        ),
    ]
    sort_columns: Annotated[
        list[SortInstruction],
        Field(
            title="Sort Instructions",
            description="ソート設定のリスト。ソートするカラム名と昇順・降順の指定を組み合わせて、複数カラムでのソートも可能です。既存カラム名から指定してください。",
            min_length=1,
        ),
    ]


class SortColumnsResult(BaseResult):
    """カラムソートレスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="ソートを実行したテーブル名",
        ),
    ]


# ---------------------------------------------------------------------------
# カラム変換
# ---------------------------------------------------------------------------


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


class TransformColumnResult(BaseResult):
    """カラム変換レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="変換カラムを追加したテーブル名",
        ),
    ]
    column_name: Annotated[
        str,
        Field(
            title="Column Name",
            description="追加した変換カラム名",
        ),
    ]


# ---------------------------------------------------------------------------
# 列型変換
# ---------------------------------------------------------------------------


class CastColumnRequestBody(BaseRequest):
    """列型変換リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description=(
                "操作対象のテーブル名。"
                "ワークスペースに存在するテーブルの中から指定してください。"
            )
        ),
    ]
    source_column_name: Annotated[
        ColumnName,
        Field(
            description=(
                "変換元となるカラム名。"
                "ワークスペースに存在するテーブルの中から指定してください。"
            )
        ),
    ]
    target_type: Annotated[
        Literal["float", "int", "str", "bool", "date", "datetime"],
        Field(
            title="Target Type",
            description=(
                "変換先のデータ型。"
                "float / int / str / bool / date / datetime から選択。"
            ),
        ),
    ]
    new_column_name: Annotated[
        NewColumnName,
        Field(
            description=(
                "新しいカラム名。"
                "既存のカラム名と重複しない名前を指定してください。"
            )
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description=(
                "追加位置のカラム名。"
                "指定したカラムの右隣に新しいカラムが追加されます。"
                "既存のカラム名から指定してください。"
            ),
        ),
    ]
    cleanup_whitespace: Annotated[
        bool,
        Field(
            title="Cleanup Whitespace",
            description=(
                "前後の空白を削除するか。変換元が文字列型の場合のみ有効。"
            ),
        ),
    ] = True
    remove_commas: Annotated[
        bool,
        Field(
            title="Remove Commas",
            description=(
                "カンマ(,)を削除するか。"
                "数値型変換時に '1,234' → '1234' のような前処理に使用。"
                "変換元が文字列型の場合のみ有効。"
            ),
        ),
    ] = True
    datetime_format: Annotated[
        str | None,
        Field(
            default=None,
            title="Datetime Format",
            examples=["%Y-%m-%d", "%Y/%m/%d %H:%M:%S"],
            description=(
                "date / datetime 変換時のパース書式。"
                "例: '%Y-%m-%d', '%Y/%m/%d'。"
                "None の場合は Polars が自動推定します。"
            ),
        ),
    ]
    strict: Annotated[
        bool,
        Field(
            title="Strict",
            description=(
                "True なら変換失敗時に 400 エラーを返す。"
                "False なら変換失敗した値を null にして処理を続行する。"
            ),
        ),
    ] = False


class CastColumnResult(BaseResult):
    """列型変換レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="型変換カラムを追加したテーブル名",
        ),
    ]
    column_name: Annotated[
        str,
        Field(
            title="Column Name",
            description="追加した型変換カラム名",
        ),
    ]


# ---------------------------------------------------------------------------
# カラムリスト取得
# ---------------------------------------------------------------------------


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


class ColumnInfo(BaseResult):
    """カラム情報"""

    name: str = Field(
        title="Name",
        description="カラム名",
    )
    type: str = Field(
        title="Type",
        description="Polarsデータ型（例: Int64, Float64, String）",
    )


class GetColumnListResult(BaseResult):
    """カラムリスト取得レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="カラムリストを取得したテーブル名",
        ),
    ]
    column_info_list: list[ColumnInfo] = Field(
        title="Column Info List",
        description="カラム情報のリスト",
    )


# ---------------------------------------------------------------------------
# 列移動
# ---------------------------------------------------------------------------


class MoveColumnRequestBody(BaseRequest):
    """列移動リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            description=(
                "操作対象のテーブル名。"
                "ワークスペースに存在するテーブルの中から指定してください。"
            )
        ),
    ]
    column_name: Annotated[
        ColumnName,
        Field(description="移動する列名。既存の列名から指定してください。"),
    ]
    anchor_column_name: Annotated[
        ColumnName | None,
        Field(
            default=None,
            description=(
                "挿入基準列名。指定した列の直前に移動列を挿入します。"
                "null を指定した場合は末尾に移動します。"
            ),
        ),
    ]

    @model_validator(mode="after")
    def _validate_columns_differ(self) -> MoveColumnRequestBody:
        if (
            self.anchor_column_name is not None
            and self.column_name == self.anchor_column_name
        ):
            raise ValueError(
                _("anchorColumnName must differ from columnName.")
            )
        return self


class MoveColumnResult(BaseResult):
    """列移動レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="列を移動したテーブル名",
        ),
    ]
    column_names: Annotated[
        list[str],
        Field(
            title="Column Names",
            description="移動後の全列名リスト（順序付き）",
        ),
    ]


# ---------------------------------------------------------------------------
# パネル時間カラム追加
# ---------------------------------------------------------------------------


class AddPanelTimeColumnRequestBody(BaseRequest):
    """パネル時間カラム追加リクエスト

    個体ID列でグループ化し、グループ内の行順に
    start_value から step ずつ増加する整数列を追加する。
    パネルデータの年次・期次変数生成に使用する。
    """

    table_name: Annotated[
        TableName,
        Field(
            description=(
                "操作対象のテーブル名。"
                "ワークスペースに存在するテーブルの中から"
                "指定してください。"
            )
        ),
    ]
    id_column: Annotated[
        ColumnName,
        Field(
            description=(
                "グループ化キーとなる個体ID列名。"
                "既存の列名から指定してください。"
            )
        ),
    ]
    new_column_name: Annotated[
        NewColumnName,
        Field(
            description=(
                "新しいカラム名。"
                "既存のカラム名と重複しない名前を指定してください。"
            )
        ),
    ]
    add_position_column: Annotated[
        ColumnName,
        Field(
            description=(
                "追加位置のカラム名。指定したカラムの右隣に"
                "新しいカラムが追加されます。"
                "既存のカラム名から指定してください。"
            ),
        ),
    ]
    start_value: Annotated[
        int,
        Field(
            default=1,
            description=(
                "各グループ内の最初の値。"
                "例: 2000 を指定すると 2000, 2001, 2002, ... となる。"
            ),
        ),
    ]
    step: Annotated[
        int,
        Field(
            default=1,
            description=(
                "増分。負の値で降順も可能。"
                "0 は禁止（全行同値になるため固定値列を使用すること）。"
            ),
        ),
    ]

    @field_validator("step")
    @classmethod
    def _validate_step_nonzero(cls, v: int) -> int:
        if v == 0:
            raise ValueError(_("step must not be 0."))
        return v


class AddPanelTimeColumnResult(BaseResult):
    """パネル時間カラム追加レスポンス"""

    table_name: Annotated[
        str,
        Field(
            title="Table Name",
            description="パネル時間カラムを追加したテーブル名",
        ),
    ]
    column_name: Annotated[
        str,
        Field(
            title="Column Name",
            description="追加したパネル時間カラム名",
        ),
    ]

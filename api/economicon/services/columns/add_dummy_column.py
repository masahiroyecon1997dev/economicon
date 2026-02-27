import re
from typing import ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import AddDummyColumnRequestBody
from economicon.models.enums import DummyMode, NullStrategy
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)

NULL_PLACEHOLDER = "__null__"


def _sanitize_col_name(value: str) -> str:
    """カラム名をサニタイズする。

    スペース・制御文字をアンダースコアに置換し、
    連続するアンダースコアを単一に圧縮する。
    """
    sanitized = re.sub(r"[\s\x00-\x1f\x7f]", "_", value)
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized.strip("_") or "_"


def _make_unique_name(base: str, existing: list[str]) -> str:
    """既存カラム名と重複しないユニーク名を生成する。

    重複する場合は末尾に _v2, _v3, ... を付与する。
    """
    if base not in existing:
        return base
    idx = 2
    while True:
        candidate = f"{base}_v{idx}"
        if candidate not in existing:
            return candidate
        idx += 1


class AddDummyColumn:
    """
    テーブルの指定列からダミー変数列を作成するAPIクラス。

    mode='single': 指定された1つの値をダミー化する。
    mode='all_except_base': 基準値を除いた全カテゴリを
        一括ダミー化する（計量経済分析用）。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "source_column_name": "sourceColumnName",
        "dummy_column_name": "dummyColumnName",
        "add_position_column": "addPositionColumn",
        "target_value": "targetValue",
        "mode": "mode",
        "drop_base_value": "dropBaseValue",
        "null_strategy": "nullStrategy",
    }

    def __init__(
        self,
        body: AddDummyColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.source_column_name = body.source_column_name
        self.dummy_column_name = body.dummy_column_name
        self.add_position_column = body.add_position_column
        self.target_value = body.target_value
        self.mode = body.mode
        self.drop_base_value = body.drop_base_value
        self.null_strategy = body.null_strategy

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 対象の列が存在することを検証
        validate_existence(
            value=self.source_column_name,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["source_column_name"],
        )
        # 追加位置の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.add_position_column,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["add_position_column"],
        )
        # single モード時のみダミー列名の重複チェック
        if self.mode == DummyMode.SINGLE:
            assert self.dummy_column_name is not None
            validate_non_existence(
                value=self.dummy_column_name,
                existing_list=column_name_list,
                target=self.PARAM_NAMES["dummy_column_name"],
            )

    def _preprocess_source(self, df: pl.DataFrame) -> pl.DataFrame:
        """ソース列の前処理。

        文字列型のカラムに対して先頭末尾の空白をトリムし、
        空文字列を null に変換する。
        """
        src = self.source_column_name
        if df[src].dtype == pl.Utf8:
            return df.with_columns(
                pl.when(pl.col(src).str.strip_chars().eq(""))
                .then(None)
                .otherwise(pl.col(src).str.strip_chars())
                .alias(src)
            )
        return df

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # ソース列の前処理（空文字・空白 → null）
            df = self._preprocess_source(df)

            if self.mode == DummyMode.SINGLE:
                return self._execute_single(df)
            else:
                return self._execute_all_except_base(df)
        except ProcessingError:
            raise
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "adding dummy column processing"
            )
            raise ProcessingError(
                error_code=(ErrorCode.ADD_DUMMY_COLUMN_PROCESS_ERROR),
                message=message,
                detail=str(e),
            ) from e

    def _execute_single(self, df: pl.DataFrame) -> dict:
        """単一値ダミー化モード。"""
        src = self.source_column_name

        # null_strategy == error のとき null が存在すれば失敗
        if self.null_strategy == NullStrategy.ERROR:
            if df[src].is_null().any():
                message = _("Null values found in the source column")
                raise ProcessingError(
                    error_code=(ErrorCode.ADD_DUMMY_COLUMN_NULL_VALUES_FOUND),
                    message=message,
                    detail=(f"Column '{src}' contains null values."),
                )

        dummy_values = (df[src] == self.target_value).cast(pl.Int32)

        current_cols = df.columns
        target_idx = current_cols.index(self.add_position_column) + 1
        new_order = (
            current_cols[:target_idx]
            + [self.dummy_column_name]
            + current_cols[target_idx:]
        )
        assert self.dummy_column_name is not None
        df_with_dummy = df.with_columns(
            dummy_values.alias(self.dummy_column_name)
        ).select(new_order)

        self.tables_store.update_table(self.table_name, df_with_dummy)
        return {
            "tableName": self.table_name,
            "addedColumnNames": [self.dummy_column_name],
        }

    def _execute_all_except_base(self, df: pl.DataFrame) -> dict:
        """基準値を除く全カテゴリ一括ダミー化モード。"""
        src = self.source_column_name
        has_null = df[src].is_null().any()

        # null_strategy == error のとき null が存在すれば失敗
        if self.null_strategy == NullStrategy.ERROR and has_null:
            message = _("Null values found in the source column")
            raise ProcessingError(
                error_code=(ErrorCode.ADD_DUMMY_COLUMN_NULL_VALUES_FOUND),
                message=message,
                detail=(
                    f"Column '{src}' contains null values. "
                    "Use null_strategy='exclude' or "
                    "'as_category'."
                ),
            )

        # ユニーク値収集（文字列表現で辞書順ソート）
        raw_unique: list[str] = sorted(
            str(v) for v in df[src].drop_nulls().unique().to_list()
        )

        # null を as_category で扱う場合は __null__ を追加
        if self.null_strategy == NullStrategy.AS_CATEGORY and has_null:
            raw_unique = sorted(raw_unique + [NULL_PLACEHOLDER])

        # ベース値の決定
        if self.drop_base_value == "auto_most_frequent":
            most_frequent_val = (
                df[src]
                .drop_nulls()
                .value_counts()
                .sort("count", descending=True)
                .row(0)[0]
            )
            base_str = str(most_frequent_val)
        else:
            base_str = str(self.drop_base_value)

        # ダミー化対象（ベース値を除外）
        target_str_vals = [v for v in raw_unique if v != base_str]

        # 挿入位置の計算
        current_cols = list(df.columns)
        insert_idx = current_cols.index(self.add_position_column) + 1
        all_existing = list(current_cols)
        added_names: list[str] = []

        for val_str in target_str_vals:
            raw_name = f"{src}_{val_str}"
            sanitized = _sanitize_col_name(raw_name)
            col_name = _make_unique_name(sanitized, all_existing)

            if val_str == NULL_PLACEHOLDER:
                dummy_series = df[src].is_null().cast(pl.Int32)
            else:
                dummy_series = (df[src] == val_str).cast(pl.Int32)

            df = df.with_columns(dummy_series.alias(col_name))
            added_names.append(col_name)
            all_existing.append(col_name)

        # 挿入位置に並べ替え
        final_order = (
            current_cols[:insert_idx] + added_names + current_cols[insert_idx:]
        )
        df = df.select(final_order)

        self.tables_store.update_table(self.table_name, df)
        return {
            "tableName": self.table_name,
            "addedColumnNames": added_names,
        }

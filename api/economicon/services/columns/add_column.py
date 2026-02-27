from typing import ClassVar

import polars as pl

from economicon.core.encodings import POLARS_ENCODING_MAP
from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import AddColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)
from economicon.utils.validators.files import (
    validate_file_format,
    validate_file_path,
)


class AddColumn:
    """
    テーブルに新しい列を追加するためのAPIクラス

    指定されたテーブルの指定された位置に新しい列を挿入します。
    新しい列は空（None）の値で初期化されます。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "new_column_name": "newColumnName",
        "add_position_column": "addPositionColumn",
        "csv_file_path": "csvFilePath",
        "separator": "separator",
    }

    def __init__(
        self,
        body: AddColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.new_column_name = body.new_column_name
        self.add_position_column = body.add_position_column
        self.csv_file_path = body.csv_file_path
        self.csv_has_header = body.csv_has_header
        self.csv_strict_row_count = body.csv_strict_row_count
        self.separator = body.separator
        self.csv_encoding = body.csv_encoding

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 追加対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 追加する列名が既存の列名と重複しないことを検証
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.PARAM_NAMES["new_column_name"],
        )
        # 追加位置の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.add_position_column,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["add_position_column"],
        )
        # CSVファイルパスが指定されている場合の追加バリデーション
        if self.csv_file_path is not None:
            validate_file_path(
                path_str=self.csv_file_path,
                target=self.PARAM_NAMES["csv_file_path"],
            )
            validate_file_format(
                path_str=self.csv_file_path,
                target=self.PARAM_NAMES["csv_file_path"],
                allowed_extensions=["csv"],
            )

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # 追加位置を計算（指定されたカラムの右隣）
            current_cols = df.columns
            target_idx = current_cols.index(self.add_position_column) + 1

            # 列の並び順を定義
            new_order = (
                current_cols[:target_idx]
                + [self.new_column_name]
                + current_cols[target_idx:]
            )

            # CSVファイルからデータを読み込むか、空列を作成するか
            if self.csv_file_path is not None:
                row_count = table_info.row_count
                # CSVファイルから列データを読み込む
                new_column_data = self._read_column_from_csv(row_count)
                # 新しい列をデータフレームに追加
                df_with_new_col = df.with_columns(
                    pl.lit(new_column_data).alias(self.new_column_name)
                ).select(new_order)
            else:
                # 新しい列を追加
                df_with_new_col = df.with_columns(
                    pl.lit(None).alias(self.new_column_name)
                ).select(new_order)

            # 新しい列をデータフレームに追加
            self.tables_store.update_table(self.table_name, df_with_new_col)
            # 結果を返す
            result = {
                "tableName": self.table_name,
                "columnName": self.new_column_name,
            }
            return result
        except ProcessingError as e:
            raise e
        except Exception as e:
            message = _(
                "An unexpected error occurred during adding column processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.ADD_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e

    def _read_column_from_csv(self, expected_rows: int):
        """
        CSVファイルから列データを読み込む

        Parameters
        ----------
        expected_rows : int
            期待される行数（テーブルの行数）

        Returns
        -------
        list
            列データのリスト

        Raises
        ------
        ProcessingError
            CSV読み込みエラー、行数不一致エラー
        """
        try:
            if self.csv_file_path is None:
                message = _("CSV file path is not specified.")
                raise ProcessingError(
                    error_code=ErrorCode.CSV_FILE_PATH_NOT_SPECIFIED,
                    message=message,
                )
            # CSVファイルを読み込む
            encoding = POLARS_ENCODING_MAP.get(
                self.csv_encoding, self.csv_encoding
            )
            skip_rows = 1 if self.csv_has_header else 0
            df_csv = pl.read_csv(
                self.csv_file_path,
                separator=self.separator,
                encoding=encoding,
                skip_rows=skip_rows,
                has_header=False,
            )

            # CSVファイルが空の場合
            if df_csv.height == 0:
                message = _("The CSV file is empty or contains no valid data.")
                raise ProcessingError(
                    error_code=ErrorCode.EMPTY_CSV_FILE,
                    message=message,
                )

            # 最初の列を取得
            # （列名はnew_column_nameを使うため、CSVの1列目だけ取得）
            if df_csv.width == 0:
                message = _("The CSV file does not contain any columns.")
                raise ProcessingError(
                    error_code=ErrorCode.NO_COLUMNS_IN_CSV_FILE,
                    message=message,
                )

            first_column = df_csv[:, 0]
            row_count = len(first_column)

            # 行数のチェックと調整
            if row_count != expected_rows:
                if self.csv_strict_row_count:
                    # 厳密モード：エラーを発生
                    message = _(
                        "Row count mismatch: CSV has {csv_rows} rows, "
                        "but table has {expected_rows} rows."
                    ).format(csv_rows=row_count, expected_rows=expected_rows)
                    raise ProcessingError(
                        error_code=ErrorCode.ROW_COUNT_MISMATCH,
                        message=message,
                    )
                # 非厳密モード：調整する
                elif row_count > expected_rows:
                    # 超過分を切り捨て
                    first_column = first_column[:expected_rows]
                else:
                    # 不足分をNoneで埋める
                    first_column = first_column.extend_constant(
                        None, expected_rows - row_count
                    )

            return first_column

        except pl.exceptions.NoDataError as e:
            message = _("The CSV file is empty or contains no valid data.")
            raise ProcessingError(
                error_code=ErrorCode.EMPTY_CSV_FILE,
                message=message,
                detail=str(e),
            ) from e
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            message = _("An unexpected error occurred during CSV processing")
            raise ProcessingError(
                error_code=ErrorCode.CSV_PROCESSING_ERROR,
                message=message,
                detail=str(e),
            ) from e

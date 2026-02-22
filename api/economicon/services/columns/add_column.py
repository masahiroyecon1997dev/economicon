import polars as pl

from ...i18n.translation import gettext as _
from ...models import AddColumnRequestBody
from ...utils import ProcessingError
from ...utils.validators import validate_existence, validate_non_existence
from ...utils.validators.files import validate_file_format, validate_file_path
from ..data.tables_store import TablesStore


class AddColumn:
    """
    テーブルに新しい列を追加するためのAPIクラス

    指定されたテーブルの指定された位置に新しい列を挿入します。
    新しい列は空（None）の値で初期化されます。
    """

    def __init__(self, AddColumnRequestBody: AddColumnRequestBody):
        self.tables_store = TablesStore()
        self.table_name = AddColumnRequestBody.table_name
        self.new_column_name = AddColumnRequestBody.new_column_name
        self.add_position_column = AddColumnRequestBody.add_position_column
        self.csv_file_path = AddColumnRequestBody.csv_file_path
        self.csv_has_header = AddColumnRequestBody.csv_has_header
        self.csv_strict_row_count = AddColumnRequestBody.csv_strict_row_count
        self.separator = AddColumnRequestBody.separator
        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "add_position_column": "addPositionColumn",
            "csv_file_path": "csvFilePath",
            "separator": "separator",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 追加対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 追加する列名が既存の列名と重複しないことを検証
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.param_names["new_column_name"],
        )
        # 追加位置の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.add_position_column,
            valid_list=column_name_list,
            target=self.param_names["add_position_column"],
        )
        # CSVファイルパスが指定されている場合の追加バリデーション
        if self.csv_file_path is not None:
            validate_file_path(
                path_str=self.csv_file_path,
                target=self.param_names["csv_file_path"],
            )
            validate_file_format(
                path_str=self.csv_file_path,
                target=self.param_names["csv_file_path"],
                allowed_extensions=["csv"],
            )
        return None

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            num_rows = table_info.row_count
            df = table_info.table

            # CSVファイルからデータを読み込むか、空列を作成するか
            if self.csv_file_path is not None:
                # CSVファイルから列データを読み込む
                new_column_data = self._read_column_from_csv(num_rows)
            else:
                # 空列を作成
                new_column_data = [None] * num_rows

            insert_index = df.columns.index(self.add_position_column) + 1
            df_with_new_col = df.insert_column(
                index=insert_index,
                column=pl.Series(self.new_column_name, new_column_data),
            )
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
                error_code="AddColumnProcessError",
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
                    error_code="CSVFilePathNotSpecified",
                    message=message,
                )
            # CSVファイルを読み込む
            skip_rows = 1 if self.csv_has_header else 0
            df_csv = pl.read_csv(
                self.csv_file_path,
                separator=self.separator,
                encoding="utf8",
                skip_rows=skip_rows,
                has_header=False,
            )

            # CSVファイルが空の場合
            if df_csv.height == 0:
                message = _("The CSV file is empty or contains no valid data.")
                raise ProcessingError(
                    error_code="EmptyCSVFile",
                    message=message,
                )

            # 最初の列を取得（列名はnew_column_nameを使うため、CSVの1列目だけ取得）
            if df_csv.width == 0:
                message = _("The CSV file does not contain any columns.")
                raise ProcessingError(
                    error_code="NoColumnsInCSVFile",
                    message=message,
                )

            first_column = df_csv[:, 0].to_list()
            csv_rows = len(first_column)

            # 行数のチェックと調整
            if csv_rows != expected_rows:
                if self.csv_strict_row_count:
                    # 厳密モード：エラーを発生
                    message = _(
                        "Row count mismatch: CSV has {csv_rows} rows, "
                        "but table has {expected_rows} rows."
                    ).format(csv_rows=csv_rows, expected_rows=expected_rows)
                    raise ProcessingError(
                        error_code="RowCountMismatch",
                        message=message,
                    )
                else:
                    # 非厳密モード：調整する
                    if csv_rows > expected_rows:
                        # 超過分を切り捨て
                        first_column = first_column[:expected_rows]
                    else:
                        # 不足分をNoneで埋める
                        first_column.extend(
                            [None] * (expected_rows - csv_rows)
                        )

            return first_column

        except pl.exceptions.NoDataError as e:
            message = _("The CSV file is empty or contains no valid data.")
            raise ProcessingError(
                error_code="EmptyCSVFile",
                message=message,
                detail=str(e),
            ) from e
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            message = _("An unexpected error occurred during CSV processing")
            raise ProcessingError(
                error_code="CSVProcessingError",
                message=message,
                detail=str(e),
            ) from e

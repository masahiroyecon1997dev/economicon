import polars as pl
from django.utils.translation import gettext as _
from typing import Dict
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator import (
    validate_file_path,
    validate_new_table_name,
    validate_separator
)
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class ImportCsvByPath(AbstractApi):
    """
    CSVファイルパス指定でデータをインポートしてテーブルを作成するAPIクラス

    指定されたパスのCSVファイルを解析し、指定されたテーブル名で登録します。
    区切り文字を指定できます。
    """

    def __init__(self, file_path: str, table_name: str, separator: str = ','):
        # テーブルマネージャーの初期化
        self.tables_manager = TablesManager()
        # ファイルパス
        self.file_path = file_path
        # テーブル名
        self.table_name = table_name
        # 区切り文字
        self.separator = separator
        # パラメータ名のマッピング
        self.param_names = {
            'file_path': 'filePath',
            'table_name': 'tableName',
            'separator': 'separator',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            # ファイルパスのバリデーション
            validate_file_path(
                self.file_path,
                self.param_names['file_path']
            )
            table_name_list = self.tables_manager.get_table_name_list()
            # テーブル名のバリデーション
            validate_new_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            # 区切り文字のバリデーション
            validate_separator(
                self.separator,
                self.param_names['separator']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # CSVファイルのインポート処理
        try:
            # CSVファイルをPolarsデータフレームに変換
            df = pl.read_csv(self.file_path,
                             separator=self.separator, encoding='utf8')

            # テーブルを作成
            created_table_name = self.tables_manager.store_table(
                self.table_name, df)

            # 結果を返す
            result = {'tableName': created_table_name}
            return result

        except pl.NoDataError as e:
            message = _("The CSV file is empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.ComputeError as e:
            message = _("Failed to parse CSV file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during CSV processing")
            raise ApiError(message) from e


def import_csv_by_path(file_path: str,
                       table_name: str, separator: str = ',') -> Dict:
    """
    CSVファイルパスからデータをインポートしてテーブルを作成する関数

    Args:
        file_path: CSVファイルのパス
        table_name: 作成するテーブル名
        separator: CSVの区切り文字（デフォルト: カンマ）

    Returns:
        作成されたテーブル名を含む辞書
    """
    api = ImportCsvByPath(file_path, table_name, separator)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # APIエラーが発生した場合はそのまま再スロー
        raise e
    return result

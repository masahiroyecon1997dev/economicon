import polars as pl
from django.utils.translation import gettext as _
from typing import Dict
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator import (
    validate_new_table_name
)
from ..utilities.validator.file_validators import (
    validate_file_path,
)
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class ImportParquetByPath(AbstractApi):
    """
    PARQUETファイルパス指定でデータをインポートしてテーブルを作成するAPIクラス

    指定されたパスのPARQUETファイルを解析し、指定されたテーブル名で登録します。
    """

    def __init__(self, file_path: str, table_name: str):
        # テーブルマネージャーの初期化
        self.tables_manager = TablesManager()
        # ファイルパス
        self.file_path = file_path
        # テーブル名
        self.table_name = table_name
        # パラメータ名のマッピング
        self.param_names = {
            'file_path': 'filePath',
            'table_name': 'tableName',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
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
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # PARQUETファイルのインポート処理
        try:
            # PARQUETファイルをPolarsデータフレームに変換
            df = pl.read_parquet(self.file_path)

            # テーブルを作成
            created_table_name = self.tables_manager.store_table(
                self.table_name, df)

            # 結果を返す
            result = {'tableName': created_table_name}
            return result

        except pl.NoDataError as e:
            message = _("The PARQUET file is empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.ComputeError as e:
            message = _("Failed to parse PARQUET file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "PARQUET processing")
            raise ApiError(message) from e


def import_parquet_by_path(file_path: str, table_name: str) -> Dict:
    """
    PARQUETファイルパスからデータをインポートしてテーブルを作成する関数

    Args:
        file_path: PARQUETファイルのパス
        table_name: 作成するテーブル名

    Returns:
        作成されたテーブル名を含む辞書
    """
    api = ImportParquetByPath(file_path, table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # APIエラーが発生した場合はそのまま再スロー
        raise e
    return result

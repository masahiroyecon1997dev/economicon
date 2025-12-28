import io
from typing import BinaryIO, Dict

import polars as pl
from django.utils.translation import gettext as _

from ..data.tables_manager import TablesManager
from ..utilities.create_table_name import create_table_name_by_file_name
from ..utilities.validator.common_validators import ValidationError
from .abstract_api import AbstractApi, ApiError


class ImportCsvByFile(AbstractApi):
    """
    CSVファイルからデータをインポートしてテーブルを作成するAPIクラス

    アップロードされたCSVファイルを解析し、新しいテーブルとして登録します。
    テーブル名はファイル名から自動生成されます。
    """

    def __init__(self, file_data: BinaryIO, file_name: str):
        # テーブルマネージャーの初期化
        self.tables_manager = TablesManager()
        # ファイルデータ
        self.file_data = file_data
        # ファイル名
        self.file_name = file_name
        # 自動生成されるテーブル名
        table_name_list = self.tables_manager.get_table_name_list()
        self.table_name = create_table_name_by_file_name(file_name,
                                                         table_name_list)
        # パラメータ名のマッピング
        self.param_names = {
            'file': 'file',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            # ファイルデータの基本チェック
            if not self.file_data or not self.file_name:
                raise ValidationError(_("File data or file name is missing"))

            # CSVファイルの拡張子チェック
            if not self.file_name.lower().endswith('.csv'):
                raise ValidationError(_("File must be a CSV file"))

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # CSVファイルのインポート処理
        try:
            # CSVファイルをPolarsデータフレームに変換
            df = pl.read_csv(io.BytesIO(self.file_data.read()))

            # テーブルを作成
            self.tables_manager.store_table(self.table_name, df)

            # 結果を返す
            result = {'tableName': self.table_name}
            return result

        except pl.exceptions.NoDataError as e:
            message = _("The uploaded CSV file is "
                        "empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.exceptions.ComputeError as e:
            message = _("Failed to parse CSV file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during CSV processing")
            raise ApiError(message) from e


def import_csv_by_file(file_data: BinaryIO, file_name: str) -> Dict:
    """
    CSVファイルからデータをインポートしてテーブルを作成する関数

    Args:
        file_data: CSVファイルのバイナリデータ
        file_name: CSVファイルの名前

    Returns:
        作成されたテーブル名を含む辞書
    """
    api = ImportCsvByFile(file_data, file_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # APIエラーが発生した場合はそのまま再スロー
        raise e
    return result

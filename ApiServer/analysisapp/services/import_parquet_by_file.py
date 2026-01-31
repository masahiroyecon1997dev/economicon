import io
from typing import BinaryIO, Dict

import polars as pl

from ..utils.create_table_name import create_table_name_by_file_name
from ..utils.validator.common_validators import ValidationError
from .abstract_api import AbstractApi, ApiError
from .data.tables_store import TablesStore
from ..i18n.translation import gettext as _


class ImportParquetByFile(AbstractApi):
    """
    Parquetファイルからデータをインポートしてテーブルを作成するAPIクラス

    アップロードされたParquetファイルを解析し、新しいテーブルとして登録します。
    テーブル名はファイル名から自動生成されます。
    """

    def __init__(self, file_data: BinaryIO | None, file_name: str | None):
        # テーブルマネージャーの初期化
        self.tables_store = TablesStore()
        # ファイルデータ
        self.file_data = file_data
        # ファイル名
        self.file_name = file_name
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
            else:
                self.validated_file_data: BinaryIO = self.file_data
                self.validated_file_name: str = self.file_name

            # Parquetファイルの拡張子チェック
            if not self.validated_file_name.lower().endswith('.parquet'):
                raise ValidationError(_("File must be a Parquet file"))

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # Parquetファイルのインポート処理
        try:
            # ParquetファイルをPolarsデータフレームに変換
            df = pl.read_parquet(io.BytesIO(self.validated_file_data.read()))

            # 自動生成されるテーブル名
            table_name_list = self.tables_store.get_table_name_list()
            self.table_name = create_table_name_by_file_name(
                self.validated_file_name, table_name_list)

            # テーブルを作成
            self.tables_store.store_table(self.table_name, df)

            # 結果を返す
            result = {'tableName': self.table_name}
            return result

        except pl.exceptions.NoDataError as e:
            message = _("The uploaded PARQUET file is "
                        "empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.exceptions.ComputeError as e:
            message = _("Failed to parse PARQUET file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during PARQUET "
                        "processing")
            raise ApiError(message) from e


def import_parquet_by_file(file_data: BinaryIO | None,
                           file_name: str | None) -> Dict:
    """
    Parquetファイルからデータをインポートしてテーブルを作成する関数

    Args:
        file_data: Parquetファイルのバイナリデータ
        file_name: Parquetファイルの名前

    Returns:
        作成されたテーブル名を含む辞書
    """
    api = ImportParquetByFile(file_data, file_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

import io
import polars as pl
from typing import Dict, BinaryIO
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.create_table_name import create_table_name_by_file_name
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class ImportExcelByFile(AbstractApi):
    """
    EXCELファイルからデータをインポートしてテーブルを作成するAPIクラス

    アップロードされたExcelファイルを解析し、新しいテーブルとして登録します。
    テーブル名はファイル名から自動生成されます。
    """

    def __init__(self, file_data: BinaryIO, file_name: str):
        self.tables_manager = TablesManager()
        # テーブルマネージャーの初期化
        self.tables_manager = TablesManager()
        # ファイルデータ
        self.file_data = file_data
        # ファイル名
        self.file_name = file_name
        # 自動生成されるテーブル名
        table_name_list = self.tables_manager.get_table_name_list()
        self.table_name = create_table_name_by_file_name(
            file_name, table_name_list)
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

            # Excelファイルの拡張子チェック
            if not (self.file_name.lower().endswith('.xlsx') or
                    self.file_name.lower().endswith('.xls')):
                raise ValidationError(_("File must be an Excel file"))

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # Excelファイルのインポート処理
        try:
            # ExcelファイルをPolarsデータフレームに変換
            df = pl.read_excel(io.BytesIO(self.file_data.read()))

            # テーブルを作成
            self.tables_manager.store_table(self.table_name, df)

            # 結果を返す
            result = {'tableName': self.table_name}
            return result

        except pl.NoDataError as e:
            message = _("The uploaded EXCEL file is empty or "
                        "contains no valid data.")
            raise ApiError(message) from e
        except pl.ComputeError as e:
            message = _("Failed to parse EXCEL file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _('An unexpected error occurred during EXCEL processing')
            raise ApiError(message) from e


def import_excel_by_file(file_data: BinaryIO, file_name: str) -> Dict:
    """
    Excelファイルからデータをインポートしてテーブルを作成する関数

    Args:
        file_data: Excelファイルのバイナリデータ
        file_name: Excelファイルの名前

    Returns:
        作成されたテーブル名を含む辞書
    """
    api = ImportExcelByFile(file_data, file_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

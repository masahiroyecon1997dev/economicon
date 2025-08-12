from typing import Optional, Dict
import polars as pl
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import Validator
from ..utilities.validator.validation_config \
    import INPUT_VALIDATOR_CONFIG

from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class ImportExcelByPath(AbstractApi):
    """
    Excelファイルパス指定でデータをインポートしてテーブルを作成するAPIクラス

    指定されたパスのExcelファイルを解析し、指定されたテーブル名で登録します。
    シート名を指定できます。
    """

    def __init__(self, file_path: str, table_name: str,
                 sheet_name: Optional[str] = None):
        # テーブルマネージャーの初期化
        self.tables_manager = TablesManager()
        # ファイルパス
        self.file_path = file_path
        # テーブル名
        self.table_name = table_name
        # シート名
        self.sheet_name = sheet_name
        # パラメータ名のマッピング
        self.param_names = {
            'file_path': 'filePath',
            'table_name': 'tableName',
            'sheet_name': 'sheetName',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            validator = Validator(param_names=self.param_names,
                                  **INPUT_VALIDATOR_CONFIG)
            # ファイルパスのバリデーション
            validator.validate_file_path(self.file_path)
            table_name_list = self.tables_manager.get_table_name_list()
            # テーブル名のバリデーション
            validator.validate_new_table_name(self.table_name, table_name_list)
            # シート名のバリデーション
            validator.validate_sheet_name(self.sheet_name)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # Excelファイルのインポート処理
        try:
            # ExcelファイルをPolarsデータフレームに変換
            if self.sheet_name:
                df = pl.read_excel(self.file_path, sheet_name=self.sheet_name)
            else:
                df = pl.read_excel(self.file_path)

            # テーブルを作成
            created_table_name = self.tables_manager.store_table(
                self.table_name, df)

            # 結果を返す
            result = {'tableName': created_table_name}
            return result

        except pl.NoDataError as e:
            message = _("The EXCEL file is empty or contains no valid data.")
            raise ApiError(message) from e
        except pl.ComputeError as e:
            message = _("Failed to parse EXCEL file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "EXCEL processing")
            raise ApiError(message) from e


def import_excel_by_path(file_path: str,
                         table_name: str,
                         sheet_name: Optional[str] = None) -> Dict:
    """
    EXCELファイルパスからデータをインポートしてテーブルを作成する関数

    Args:
        file_path: EXCELファイルのパス
        table_name: 作成するテーブル名
        sheet_name: シート名（デフォルト: None）

    Returns:
        作成されたテーブル名を含む辞書
    """
    api = ImportExcelByPath(file_path, table_name, sheet_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # APIエラーが発生した場合はそのまま再スロー
        raise e
    return result

from django.utils.translation import gettext as _
from typing import Dict
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import InputValidator
from ..utilities.validator.validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError
import os


class ExportCsvByPath(AbstractApi):
    """
    テーブルをCSVファイルパス指定でエクスポートするAPIクラス

    指定されたテーブル名のデータを指定されたパスにCSVファイルとして出力します。
    区切り文字を指定できます。
    """

    def __init__(self, table_name: str, file_path: str, separator: str = ','):
        # テーブルマネージャーの初期化
        self.tables_manager = TablesManager()
        # テーブル名
        self.table_name = table_name
        # ファイルパス
        self.file_path = file_path
        # 区切り文字
        self.separator = separator
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'tableName',
            'file_path': 'filePath',
            'separator': 'separator',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            # テーブル名のバリデーション
            table_name_list = self.tables_manager.get_table_name_list()
            validator.validate_existed_table_name(self.table_name,
                                                  table_name_list)

            # ファイルパスのバリデーション
            output_dir = os.path.dirname(self.file_path)
            validator.validate_directory_path(output_dir)

            # 区切り文字のバリデーション
            validator.validate_separator(self.separator)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # CSVファイルのエクスポート処理
        try:
            # テーブルを取得
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # CSVファイルに書き込み
            df.write_csv(self.file_path, separator=self.separator)

            # 結果を返す
            result = {'filePath': self.file_path}
            return result

        except KeyError as e:
            message = _("Table does not exist: {}").format(self.table_name)
            raise ApiError(message) from e
        except PermissionError as e:
            message = _("Permission denied: Cannot write to "
                        "the specified path.")
            raise ApiError(message) from e
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "CSV export processing")
            raise ApiError(message) from e


def export_csv_by_path(table_name: str,
                       file_path: str, separator: str = ',') -> Dict:
    """
    テーブルをCSVファイルパスに出力する関数

    Args:
        table_name: エクスポートするテーブル名
        file_path: 出力するCSVファイルのパス
        separator: CSVの区切り文字（デフォルト: カンマ）

    Returns:
        出力されたファイルパスを含む辞書
    """
    api = ExportCsvByPath(table_name, file_path, separator)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # APIエラーが発生した場合はそのまま再スロー
        raise e
    return result

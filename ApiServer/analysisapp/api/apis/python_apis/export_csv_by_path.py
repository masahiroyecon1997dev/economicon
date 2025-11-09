from django.utils.translation import gettext as _
from typing import Dict
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator import (
    validate_existed_table_name
)
from ..utilities.validator.file_validators import (
    validate_directory_path,
    validate_file_name,
    validate_separator
)
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError
import os


class ExportCsvByPath(AbstractApi):
    """
    テーブルをCSVファイルパス指定でエクスポートするAPIクラス

    指定されたテーブル名のデータを指定されたパスにCSVファイルとして出力します。
    区切り文字を指定できます。
    """

    def __init__(self, table_name: str, directory_path: str,
                 file_name: str, separator: str = ','):
        # テーブルマネージャーの初期化
        self.tables_manager = TablesManager()
        # テーブル名
        self.table_name = table_name
        # ディレクトリパス
        self.directory_path = directory_path
        # ファイル名
        self.file_name = file_name
        # 区切り文字
        self.separator = separator
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'tableName',
            'directory_path': 'directoryPath',
            'file_name': 'fileName',
            'separator': 'separator',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            # テーブル名のバリデーション
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # ディレクトリパスのバリデーション
            validate_directory_path(
                self.directory_path,
                self.param_names['directory_path']
            )

            # ファイル名のバリデーション
            validate_file_name(
                self.file_name,
                self.param_names['file_name']
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
        # CSVファイルのエクスポート処理
        try:
            # テーブルを取得
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            file_path = os.path.join(self.directory_path, self.file_name)

            # CSVファイルに書き込み
            df.write_csv(file_path, separator=self.separator)

            # 結果を返す
            result = {'filePath': file_path}
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
                       directory_path: str,
                       file_name: str,
                       separator: str = ',') -> Dict:
    """
    テーブルをCSVファイルパスに出力する関数

    Args:
        table_name: エクスポートするテーブル名
        file_path: 出力するCSVファイルのパス
        separator: CSVの区切り文字（デフォルト: カンマ）

    Returns:
        出力されたファイルパスを含む辞書
    """
    api = ExportCsvByPath(table_name, directory_path, file_name, separator)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # APIエラーが発生した場合はそのまま再スロー
        raise e
    return result

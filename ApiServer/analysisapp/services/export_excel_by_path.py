import os
from typing import Dict

from ..utils.validator.common_validators import ValidationError
from ..utils.validator.file_validators import (validate_directory_path,
                                               validate_file_name)
from ..utils.validator.tables_store_validator import \
    validate_existed_table_name
from .abstract_api import AbstractApi, ApiError
from .data.tables_store import TablesStore
from ..i18n.translation import gettext as _


class ExportExcelByPath(AbstractApi):
    """
    テーブルをEXCELファイルパス指定でエクスポートするAPIクラス

    指定されたテーブル名のデータを指定されたパスにEXCELファイルとして出力します。
    """

    def __init__(self, table_name: str, directory_path: str,
                 file_name: str):
        # テーブルマネージャーの初期化
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = table_name
        # ディレクトリパス
        self.directory_path = directory_path
        # ファイル名
        self.file_name = file_name
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'tableName',
            'directory_path': 'directoryPath',
            'file_name': 'fileName',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            # テーブル名のバリデーション
            table_name_list = self.tables_store.get_table_name_list()
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

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # EXCELファイルのエクスポート処理
        try:
            # テーブルを取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            file_path = os.path.join(self.directory_path, self.file_name)

            # EXCELファイルに書き込み
            df.write_excel(file_path)

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
                        "EXCEL export processing")
            raise ApiError(message) from e


def export_excel_by_path(table_name: str,
                         directory_path: str,
                         file_name: str) -> Dict:
    """
    テーブルをEXCELファイルパスに出力する関数

    Args:
        table_name: エクスポートするテーブル名
        directory_path: 出力するディレクトリパス
        file_name: 出力するEXCELファイル名

    Returns:
        出力されたファイルパスを含む辞書
    """
    api = ExportExcelByPath(table_name, directory_path, file_name)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    try:
        result = api.execute()
    except ApiError as e:
        # APIエラーが発生した場合はそのまま再スロー
        raise e
    return result

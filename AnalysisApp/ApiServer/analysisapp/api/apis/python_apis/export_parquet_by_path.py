from django.utils.translation import gettext as _
from typing import Dict
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator \
    import TablesManagerValidator
from ..utilities.validator.validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError
import os


class ExportParquetByPath(AbstractApi):
    """
    テーブルをPARQUETファイルパス指定でエクスポートするAPIクラス

    指定されたテーブル名のデータを指定されたパスにPARQUETファイルとして出力します。
    """

    def __init__(self, table_name: str, directory_path: str,
                 file_name: str):
        # テーブルマネージャーの初期化
        self.tables_manager = TablesManager()
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
            tables_manager_validator = TablesManagerValidator(
                param_names=self.param_names,
                **INPUT_VALIDATOR_CONFIG
            )
            # テーブル名のバリデーション
            table_name_list = self.tables_manager.get_table_name_list()
            tables_manager_validator.validate_existed_table_name(
                self.table_name,
                table_name_list
            )

            # ディレクトリパスのバリデーション
            tables_manager_validator.validate_directory_path(
                self.directory_path
            )

            # ファイル名のバリデーション
            tables_manager_validator.validate_file_name(
                self.file_name
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # PARQUETファイルのエクスポート処理
        try:
            # テーブルを取得
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            file_path = os.path.join(self.directory_path, self.file_name)

            # PARQUETファイルに書き込み
            df.write_parquet(file_path)

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
                        "PARQUET export processing")
            raise ApiError(message) from e


def export_parquet_by_path(table_name: str,
                           directory_path: str,
                           file_name: str) -> Dict:
    """
    テーブルをPARQUETファイルパスに出力する関数

    Args:
        table_name: エクスポートするテーブル名
        directory_path: 出力するディレクトリパス
        file_name: 出力するPARQUETファイル名

    Returns:
        出力されたファイルパスを含む辞書
    """
    api = ExportParquetByPath(table_name, directory_path, file_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    try:
        result = api.execute()
    except ApiError as e:
        # APIエラーが発生した場合はそのまま再スロー
        raise e
    return result

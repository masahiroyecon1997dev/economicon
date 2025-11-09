import os
from datetime import datetime
from typing import Dict

from django.utils.translation import gettext as _

from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.file_validators import (
    validate_directory_path, validate_directory_path_is_directory)
from .common_api_class import AbstractApi, ApiError


class GetFiles(AbstractApi):
    """
    指定されたディレクトリ内のファイルとフォルダ一覧を取得するAPIクラス

    指定されたパス内の全てのファイルとフォルダの情報を取得します。
    各項目について、ファイル/フォルダ判定、サイズ、更新日時を含みます。
    """
    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.param_names = {
            'directory_path': 'directoryPath'
        }

    def validate(self):
        try:
            # ディレクトリパスのバリデーション
            validate_directory_path(
                self.directory_path,
                self.param_names['directory_path']
            )

            # 実際にディレクトリかどうか確認
            validate_directory_path_is_directory(self.directory_path)

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            files = []

            # ディレクトリ内のアイテムを取得
            for item_name in os.listdir(self.directory_path):
                item_path = os.path.join(self.directory_path, item_name)

                # ファイル情報を取得
                stat_info = os.stat(item_path)
                is_file = os.path.isfile(item_path)
                file_size = stat_info.st_size if is_file else 0
                modified_time = datetime.fromtimestamp(
                    stat_info.st_mtime).isoformat()

                item_info = {
                    'name': item_name,
                    'isFile': is_file,
                    'size': file_size,
                    'modifiedTime': modified_time
                }
                files.append(item_info)

            # 名前順でソート
            files.sort(key=lambda x: x['name'])

            result = {
                'directoryPath': self.directory_path,
                'files': files
            }
            return result

        except Exception as e:
            message = _("An unexpected error occurred "
                        "during listing files processing")
            raise ApiError(message) from e


def get_files(directory_path: str) -> Dict:
    api = GetFiles(directory_path)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()

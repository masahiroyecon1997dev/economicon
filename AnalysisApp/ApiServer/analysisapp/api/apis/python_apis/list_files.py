import os
from datetime import datetime
from django.utils.translation import gettext as _
from typing import Dict, List
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator import (
    validate_directory_path
)
from .common_api_class import (AbstractApi, ApiError)


class ListFiles(AbstractApi):
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
            if not os.path.isdir(self.directory_path):
                message = _(f"Path is not a directory: {self.directory_path}")
                raise ValidationError(message)
                
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            items = []
            
            # ディレクトリ内のアイテムを取得
            for item_name in os.listdir(self.directory_path):
                item_path = os.path.join(self.directory_path, item_name)
                
                # ファイル情報を取得
                stat_info = os.stat(item_path)
                is_file = os.path.isfile(item_path)
                file_size = stat_info.st_size if is_file else 0
                modified_time = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                
                item_info = {
                    'name': item_name,
                    'isFile': is_file,
                    'size': file_size,
                    'modifiedTime': modified_time
                }
                items.append(item_info)
            
            # 名前順でソート
            items.sort(key=lambda x: x['name'])
            
            result = {
                'directoryPath': self.directory_path,
                'items': items
            }
            return result
            
        except Exception as e:
            message = _("An unexpected error occurred "
                        "during listing files processing")
            raise ApiError(message) from e


def list_files(directory_path: str) -> Dict:
    api = ListFiles(directory_path)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
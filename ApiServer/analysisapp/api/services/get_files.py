import os
from datetime import datetime
from typing import Dict

from .django_compat import gettext as _

from ..utils.validator.common_validators import ValidationError
from ..utils.validator.file_validators import (
    validate_directory_path, validate_directory_path_is_directory)
from .abstract_api import AbstractApi, ApiError


class GetFiles(AbstractApi):
    """
    謖・ｮ壹＆繧後◆繝・ぅ繝ｬ繧ｯ繝医Μ蜀・・繝輔ぃ繧､繝ｫ縺ｨ繝輔か繝ｫ繝荳隕ｧ繧貞叙蠕励☆繧帰PI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝代せ蜀・・蜈ｨ縺ｦ縺ｮ繝輔ぃ繧､繝ｫ縺ｨ繝輔か繝ｫ繝縺ｮ諠・ｱ繧貞叙蠕励＠縺ｾ縺吶・    蜷・・岼縺ｫ縺､縺・※縲√ヵ繧｡繧､繝ｫ/繝輔か繝ｫ繝蛻､螳壹√し繧､繧ｺ縲∵峩譁ｰ譌･譎ゅｒ蜷ｫ縺ｿ縺ｾ縺吶・    """
    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.param_names = {
            'directory_path': 'directoryPath'
        }

    def validate(self):
        try:
            # 繝・ぅ繝ｬ繧ｯ繝医Μ繝代せ縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
            validate_directory_path(
                self.directory_path,
                self.param_names['directory_path']
            )

            # 螳滄圀縺ｫ繝・ぅ繝ｬ繧ｯ繝医Μ縺九←縺・°遒ｺ隱・            validate_directory_path_is_directory(self.directory_path)

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            files = []

            # 繝・ぅ繝ｬ繧ｯ繝医Μ蜀・・繧｢繧､繝・Β繧貞叙蠕・            for item_name in os.listdir(self.directory_path):
                item_path = os.path.join(self.directory_path, item_name)

                # 繝輔ぃ繧､繝ｫ諠・ｱ繧貞叙蠕・                stat_info = os.stat(item_path)
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

            # 蜷榊燕鬆・〒繧ｽ繝ｼ繝・            files.sort(key=lambda x: x['name'])

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

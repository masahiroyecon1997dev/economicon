from typing import Dict

from .django_compat import gettext as _

from .data.settings_manager import SettingsManager
from .abstract_api import AbstractApi, ApiError


class GetSettings(AbstractApi):
    """
    繧｢繝励Μ繧ｱ繝ｼ繧ｷ繝ｧ繝ｳ險ｭ螳壹ｒ蜿門ｾ励☆繧九◆繧√・API繧ｯ繝ｩ繧ｹ

    SettingsManager縺九ｉ險ｭ螳壽ュ蝣ｱ繧貞叙蠕励＠縺ｦ霑斐＠縺ｾ縺吶・    """

    def __init__(self):
        self.settings_manager = SettingsManager()

    def validate(self):
        # 險ｭ螳壼叙蠕励↓縺ｯ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ縺ｯ荳崎ｦ・        return None

    def execute(self):
        try:
            # SettingsManager縺九ｉ險ｭ螳壹ｒ蜿門ｾ・            settings_info = self.settings_manager.get_settings()

            # 邨先棡繧定ｿ斐☆
            return settings_info.to_dict()

        except Exception as e:
            message = _("An unexpected error occurred "
                        "during getting settings processing")
            raise ApiError(message) from e


def get_setting() -> Dict:
    """
    繧｢繝励Μ繧ｱ繝ｼ繧ｷ繝ｧ繝ｳ險ｭ螳壹ｒ蜿門ｾ励☆繧矩未謨ｰ

    Returns:
        Dict: 險ｭ螳壽ュ蝣ｱ繧貞性繧霎樊嶌
            - osName: 繧ｯ繝ｩ繧､繧｢繝ｳ繝・S縺ｮ蜷榊燕
            - defaultFolderPath: 繝輔ぃ繧､繝ｫ隱ｭ縺ｿ霎ｼ縺ｿ繧偵☆繧九ヵ繧ｩ繝ｫ繝繝代せ縺ｮ蛻晄悄蛟､
            - displayRows: 繝・・繝悶Ν縺ｫ陦ｨ遉ｺ縺吶ｋ陦梧焚
            - appLanguage: 繧｢繝励Μ繧ｱ繝ｼ繧ｷ繝ｧ繝ｳ縺ｮ陦ｨ遉ｺ險隱・            - encoding: 繝輔ぃ繧､繝ｫ隱ｭ縺ｿ霎ｼ縺ｿ譎ゅ・繝・ヵ繧ｩ繝ｫ繝医お繝ｳ繧ｳ繝ｼ繝・ぅ繝ｳ繧ｰ
            - pathSeparator: 繝代せ蛹ｺ蛻・ｊ譁・ｭ・    """
    api = GetSettings()
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()

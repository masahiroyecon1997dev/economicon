"""i18nパッケージ初期化"""

from .translation import _, get_locale_from_settings, gettext

__all__ = ["_", "gettext", "get_locale_from_settings"]

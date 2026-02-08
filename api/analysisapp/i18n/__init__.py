"""i18nパッケージ初期化"""
from .translation import _, get_locale_from_settings, gettext, gettext_lazy

__all__ = [
    '_',
    'gettext',
    'gettext_lazy',
    'get_locale_from_settings'
]

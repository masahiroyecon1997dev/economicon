"""国際化（i18n）サポート"""
import gettext
from pathlib import Path
from typing import Optional
from contextvars import ContextVar

LOCALE_DIR = Path(__file__).parent.parent / 'locale'
_current_locale: ContextVar[str] = ContextVar('current_locale', default='ja')
_translations: dict[str, gettext.GNUTranslations] = {}


def set_locale(locale: str) -> None:
    """現在のロケールを設定"""
    _current_locale.set(locale)


def get_locale() -> str:
    """現在のロケールを取得"""
    return _current_locale.get()


def _get_translation(locale: Optional[str] = None) -> gettext.GNUTranslations:
    """翻訳オブジェクトを取得"""
    if locale is None:
        locale = get_locale()

    if locale not in _translations:
        try:
            _translations[locale] = gettext.translation(
                'django',
                localedir=str(LOCALE_DIR),
                languages=[locale]
            )
        except FileNotFoundError:
            _translations[locale] = gettext.NullTranslations()

    return _translations[locale]


def gettext_lazy(message: str, locale: Optional[str] = None) -> str:
    """メッセージを翻訳"""
    translation = _get_translation(locale)
    return translation.gettext(message)


_ = gettext_lazy

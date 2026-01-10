"""国際化（i18n）サポート - fastapi-babel統合版"""
import gettext
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

# fastapi-babelの翻訳関数をインポート
from fastapi_babel import _ as babel_gettext

# 旧ロケールディレクトリ（後方互換性のため保持）
LOCALE_DIR = Path(__file__).parent.parent / 'locale'
_current_locale: ContextVar[str] = ContextVar('current_locale', default='ja')
_translations: dict[str, gettext.GNUTranslations] = {}


def set_locale(locale: str) -> None:
    """現在のロケールを設定（後方互換性のため保持）"""
    _current_locale.set(locale)


def get_locale() -> str:
    """現在のロケールを取得（後方互換性のため保持）"""
    return _current_locale.get()


def _get_translation(locale: Optional[str] = None) -> gettext.GNUTranslations:
    """翻訳オブジェクトを取得（後方互換性のため保持）"""
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
            gettext.NullTranslations()

    return _translations[locale]


def gettext_lazy(message: str, locale: Optional[str] = None) -> str:
    """メッセージを翻訳

    fastapi-babelの翻訳関数を使用します。
    locale引数は後方互換性のため保持されていますが、
    fastapi-babelが自動的にリクエストコンテキストから言語を検出します。
    """
    return babel_gettext(message)


# fastapi-babelの翻訳関数をエクスポート
_ = babel_gettext

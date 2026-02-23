"""国際化(i18n)サポート - fastapi-babel統合版

SettingsStoreからロケール設定を取得し、fastapi-babelと統合します。
リクエストコンテキスト外でも動作するように、独自の翻訳関数も提供します。
"""

import gettext as gettext_module
from pathlib import Path

from fastapi_babel import _ as babel_gettext

from ..services.data.settings_store import SettingsStore

# ロケールディレクトリ
LOCALE_DIR = Path(__file__).parent.parent / "locales"
_translations: dict[
    str, gettext_module.NullTranslations | gettext_module.GNUTranslations
] = {}


def get_locale_from_settings() -> str:
    """
    SettingsStoreから現在のロケールを取得

    この関数はfastapi-babelのget_locale関数をオーバーライドするために
    使用します。リクエストヘッダーではなく、常にSettingsStoreの
    設定値を返します。

    Returns:
        str: 現在のロケール("ja", "en"など)
    """
    # 循環インポートを避けるため、関数内でインポート

    try:
        settings_manager = SettingsStore()
        settings = settings_manager.get_settings()
        return settings.language
    except Exception:
        # 設定が初期化されていない場合はデフォルトで"ja"を返す
        return "ja"


def _get_translation(
    locale: str | None = None,
) -> gettext_module.NullTranslations | gettext_module.GNUTranslations:
    """
    指定されたロケールの翻訳オブジェクトを取得

    Args:
        locale: ロケール(指定しない場合はSettingsStoreから取得)

    Returns:
        NullTranslations | GNUTranslations: 翻訳オブジェクト
    """
    if locale is None:
        locale = get_locale_from_settings()

    # テスト環境でデフォルトで日本語を使用
    if locale is None or locale == "":
        locale = "ja"

    if locale not in _translations:
        try:
            _translations[locale] = gettext_module.translation(
                "messages", localedir=str(LOCALE_DIR), languages=[locale]
            )
        except FileNotFoundError:
            # 翻訳ファイルが見つからない場合はNullTranslationsを使用
            _translations[locale] = gettext_module.NullTranslations()

    return _translations[locale]


def gettext(message: str, locale: str | None = None) -> str:
    """
    メッセージを翻訳

    リクエストコンテキスト内外で動作します。
    コンテキスト外では、SettingsStoreから直接ロケールを取得します。

    Args:
        message: 翻訳するメッセージ
        locale: 翻訳先のロケール(省略時はSettingsStoreから取得)

    Returns:
        str: 翻訳されたメッセージ
    """
    # リクエストコンテキスト内であればfastapi-babelを使用を試みる
    try:
        return babel_gettext(message)
    except LookupError:
        # コンテキスト外の場合は独自の翻訳関数を使用
        translation = _get_translation(locale)
        return translation.gettext(message)


# 翻訳関数のエイリアス
_ = gettext

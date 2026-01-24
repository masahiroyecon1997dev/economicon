"""Django互換の翻訳関数

実際の翻訳はanalysisapp.i18n.translationモジュールから行います。
"""
from analysisapp.i18n.translation import gettext

# Django互換のための関数エイリアス
_ = gettext

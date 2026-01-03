"""

"""


def gettext(message: str) -> str:
    """翻訳関数のダミー実装
    Parameters
    ----------
    message : str
        翻訳対象の文字列
    Returns
    -------
    str
        翻訳後の文字列
    Note
    ----
    This is a dummy implementation. For actual translation, refer to ../i18n directory.
    """
    return message


# Django互換のための関数
_ = gettext

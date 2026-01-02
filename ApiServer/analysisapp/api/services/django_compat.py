"""Django鄙ｻ險ｳ髢｢謨ｰ縺ｮ莠呈鋤繝ｩ繝・ヱ繝ｼ

python_apis縺ｧ菴ｿ逕ｨ縺吶ｋ縺溘ａ縺ｮgettext莠呈鋤髢｢謨ｰ
"""


def gettext(message: str) -> str:
    """繝｡繝・そ繝ｼ繧ｸ繧定ｿ斐☆・育ｿｻ險ｳ縺ｯ陦後ｏ縺ｪ縺・ｰ｡譏鍋沿・・
    Parameters
    ----------
    message : str
        繝｡繝・そ繝ｼ繧ｸ

    Returns
    -------
    str
        繝｡繝・そ繝ｼ繧ｸ・医◎縺ｮ縺ｾ縺ｾ・・
    Note
    ----
    蠢・ｦ√↓蠢懊§縺ｦ ../i18n 繝｢繧ｸ繝･繝ｼ繝ｫ繧剃ｽｿ逕ｨ縺励※鄙ｻ險ｳ讖溯・繧貞ｮ溯｣・庄閭ｽ
    """
    return message


# Django莠呈鋤縺ｮ繧ｨ繧､繝ｪ繧｢繧ｹ
_ = gettext

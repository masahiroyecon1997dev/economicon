from economicon.i18n import _  # i18nにある翻訳関数をインポート

# Pydanticエラータイプと日本語テンプレートのマッピング
VALIDATION_ERROR_TEMPLATES = {
    "missing": _("{field}は必須項目です。"),
    "string_type": _("{field}は文字列で入力してください。"),
    "int_type": _("{field}は整数で入力してください。"),
    "float_type": _("{field}は数値で入力してください。"),
    "bool_type": _("{field}は真偽値で入力してください。"),
    "list_type": _("{field}はリスト形式で入力してください。"),
    "dict_type": _("{field}は辞書形式で入力してください。"),
    "string_too_short": _("{field}は{min_length}文字以上で入力してください。"),
    "string_too_long": _("{field}は{max_length}文字以内で入力してください。"),
    "too_short": _("{field}は{min_length}件以上ある必要があります。"),
    "less_than": _("{field}は{lt}未満で入力してください。"),
    "less_than_equal": _("{field}は{le}以下で入力してください。"),
    "greater_than": _("{field}は{gt}より大きい値で入力してください。"),
    "greater_than_equal": _("{field}は{ge}以上で入力してください。"),
    "literal_error": _(
        "{field}は次のいずれかである必要があります: {expected}"
    ),
    "union_tag_not_found": _(
        "{field}のタイプ（method等）が正しくありません。"
    ),
    "string_pattern_mismatch": _(
        "{field}に使用できない文字が含まれています。"
    ),
    "value_error": "{msg}",  # カスタムバリデータのメッセージをそのまま使う
}

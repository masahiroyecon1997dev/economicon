from economicon.i18n import _

VALIDATION_ERROR_TEMPLATES = {
    "missing": _("{field} is required"),
    "string_type": _("{field} must be a string"),
    "int_type": _("{field} must be an integer"),
    "float_type": _("{field} must be a number"),
    "bool_type": _("{field} must be a boolean"),
    "list_type": _("{field} must be a list"),
    "dict_type": _("{field} must be a dictionary"),
    "string_too_short": _("{field} must be at least {min_length} characters"),
    "string_too_long": _("{field} must be at most {max_length} characters"),
    "too_short": _("{field} must have at least {min_length} items"),
    "less_than": _("{field} must be less than {lt}"),
    "less_than_equal": _("{field} must be less than or equal to {le}"),
    "greater_than": _("{field} must be greater than {gt}"),
    "greater_than_equal": _("{field} must be greater than or equal to {ge}"),
    "literal_error": _("{field} must be one of: {expected}"),
    "union_tag_not_found": _("{field} has an invalid type"),
    "string_pattern_mismatch": _("{field} contains invalid characters"),
    "value_error": "{msg}",  # カスタムバリデータのメッセージをそのまま使う
}

from pydantic_core import ErrorDetails

from economicon.core.messages import VALIDATION_ERROR_TEMPLATES


def get_localized_message(error: ErrorDetails) -> str:
    error_type = error.get("type")
    ctx = error.get("ctx", {})
    loc = error.get("loc", [])

    # "body"を除いたフィールドパスを作成
    field_name = ".".join([str(x) for x in loc if x != "body"])

    template = VALIDATION_ERROR_TEMPLATES.get(error_type)
    if template:
        msg = error.get("msg", "")
        # Pydantic は ValueError のメッセージに "Value error, " を
        # 自動付与するため除去する
        if (
            error_type == "value_error"
            and isinstance(msg, str)
            and msg.startswith("Value error, ")
        ):
            msg = msg[len("Value error, ") :]
        # ctxの中身、フィールド名、元のメッセージを混ぜてフォーマット
        format_kwargs = {
            **ctx,
            "field": field_name,
            "msg": msg,
        }
        return template.format(**format_kwargs)
    return error.get("msg", "Validation error")

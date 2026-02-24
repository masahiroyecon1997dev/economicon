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
        # ctxの中身、フィールド名、元のメッセージを混ぜてフォーマット
        format_kwargs = {**ctx, "field": field_name, "msg": error.get("msg")}
        return template.format(**format_kwargs)
    return error.get("msg", "Validation error")

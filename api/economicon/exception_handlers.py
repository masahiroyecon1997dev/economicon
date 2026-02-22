# economicon/api/exception_handlers.py
from fastapi import FastAPI, Request
from fastapi import status as http_status
from fastapi.exceptions import RequestValidationError

from .core import get_localized_message
from .core.enums import ErrorCode
from .i18n import _
from .utils import (
    ProcessingError,
    ValidationError,
    create_error_response,
)


def init_exception_handlers(app: FastAPI):
    """
    appを受け取って、各種エラーハンドラを登録する関数
    """

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request, exc: RequestValidationError
    ):
        errors = exc.errors()

        # detailsの中に「日本語化されたエラー文字列のリスト」を作成
        localized_errors = [get_localized_message(e) for e in errors]

        return create_error_response(
            http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code=ErrorCode.VALIDATION_ERROR,
            message=localized_errors[0],
            details=localized_errors,
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST, exc.error_code, exc.message
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        # ロジックで発生した ValueError を 400 Bad Request としてフロントに返す
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST, "VALUE_ERROR", str(exc)
        )

    @app.exception_handler(ProcessingError)
    async def api_error_handler(request: Request, exc: ProcessingError):
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            exc.error_code,
            exc.message,
        )

    @app.exception_handler(NotImplementedError)
    async def not_implemented_error_handler(
        request: Request, exc: NotImplementedError
    ):
        message = _("regression is not yet implemented")
        return create_error_response(
            http_status.HTTP_501_NOT_IMPLEMENTED, "NOT_IMPLEMENTED", message
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # 予期せぬエラー
        message = _("An unexpected error occurred during processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            "UNEXPECTED_ERROR",
            message,
        )

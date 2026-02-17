# economicon/api/exception_handlers.py
from fastapi import FastAPI, Request
from fastapi import status as http_status

from .i18n import _
from .utils import ProcessingError, ValidationError, create_error_response


def init_exception_handlers(app: FastAPI):
    """
    appを受け取って、各種エラーハンドラを登録する関数
    """

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST, exc.error_code, exc.message
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

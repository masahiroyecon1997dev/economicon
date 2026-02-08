# economicon/api/exception_handlers.py
from fastapi import FastAPI, Request
from fastapi import status as http_status

from .i18n import _
from .services import ApiError
from .utils import create_error_response
from .utils.validators import ValidationError


def init_exception_handlers(app: FastAPI):
    """
    appを受け取って、各種エラーハンドラを登録する関数
    """

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST, exc.message
        )

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR, exc.message
        )

    @app.exception_handler(NotImplementedError)
    async def not_implemented_error_handler(
        request: Request, exc: NotImplementedError
    ):
        message = _("regression is not yet implemented")
        return create_error_response(
            http_status.HTTP_501_NOT_IMPLEMENTED, message
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # 予期せぬエラー
        message = _("An unexpected error occurred during processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR, message, exc
        )

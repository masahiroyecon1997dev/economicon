"""FastAPI用レスポンス作成ヘルパー関数"""

from typing import Any, Optional

from fastapi.responses import JSONResponse, Response

from .logging import (
    create_log_api_error,
    create_log_api_exception,
    create_log_api_success,
)


def create_success_response(
    status_code: int, response_object: Any
) -> JSONResponse:
    """成功レスポンスを作成"""
    result = {"code": "OK", "result": response_object}
    create_log_api_success()
    return JSONResponse(content=result, status_code=status_code)


def create_success_binary_response(
    status_code: int, binary_data: bytes, content_type: str
) -> Response:
    """成功バイナリレスポンスを作成"""
    create_log_api_success()
    return Response(
        content=binary_data, status_code=status_code, media_type=content_type
    )


def create_error_response(
    status_code: int, message: str, exception_message: Optional[Any] = None
) -> JSONResponse:
    """エラーレスポンスを作成"""
    result = {"code": "NG", "message": message}
    create_log_api_error(message)
    if exception_message is not None:
        create_log_api_exception(exception_message)
    return JSONResponse(content=result, status_code=status_code)

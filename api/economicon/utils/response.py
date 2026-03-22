"""FastAPI用レスポンス作成ヘルパー関数"""

from typing import Any, TypeVar

from fastapi.responses import JSONResponse, Response

from economicon.utils.logging import (
    log_error,
)

T = TypeVar("T")


def create_success_response(
    *, status_code: int, response_object: dict | bytes | None
) -> JSONResponse:
    """成功レスポンスを作成"""
    result = {"code": "OK", "result": response_object}
    return JSONResponse(content=result, status_code=status_code)


def create_success_binary_response(
    *, status_code: int, binary_data: bytes, content_type: str
) -> Response:
    """成功バイナリレスポンスを作成"""
    return Response(
        content=binary_data, status_code=status_code, media_type=content_type
    )


def create_error_response(
    *,
    status_code: int,
    error_code: str,  # str または ErrorCode Enum
    message: str,
    details: list[str] | None = None,  # バリデーションエラー用を統合
    exception: Exception | None = None,
) -> JSONResponse:
    """
    エラーレスポンスを作成
    バリデーションエラー(422)や業務エラー(400)、システムエラー(500)で共用
    """
    log_error(message=message, error_code=error_code)
    result: dict[str, Any] = {
        "code": error_code,
        "message": message,
    }

    if details is not None:
        result["details"] = details

    return JSONResponse(content=result, status_code=status_code)

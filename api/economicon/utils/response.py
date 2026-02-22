"""FastAPI用レスポンス作成ヘルパー関数"""

from typing import Any, Dict, List, Optional, TypeVar

from fastapi.responses import JSONResponse, Response

from .logging import (
    create_log_api_error,
    create_log_api_exception,
    create_log_api_success,
)

T = TypeVar("T")


def create_success_response(
    *, status_code: int, response_object: dict | bytes | None
) -> JSONResponse:
    """成功レスポンスを作成"""
    result = {"code": "OK", "result": response_object}
    create_log_api_success()
    return JSONResponse(content=result, status_code=status_code)


def create_success_binary_response(
    *, status_code: int, binary_data: bytes, content_type: str
) -> Response:
    """成功バイナリレスポンスを作成"""
    create_log_api_success()
    return Response(
        content=binary_data, status_code=status_code, media_type=content_type
    )


def create_error_response(
    *,
    status_code: int,
    error_code: str,  # error_code に統一
    message: str,
    details: Optional[List[str]] = None,  # バリデーションエラー用を統合
    exception: Optional[
        Exception
    ] = None,  # 文字列より Exception オブジェクトを受け取る方がロギングに有利
) -> JSONResponse:
    """
    エラーレスポンスを作成
    バリデーションエラー(422)や業務エラー(400)、システムエラー(500)で共用
    """
    result: Dict[str, Any] = {
        "code": error_code,
        "message": message,
    }

    if details is not None:
        result["details"] = details

    # ロギング処理
    create_log_api_error(message)
    if exception is not None:
        # ロギング側でスタックトレースを処理できるよう、オブジェクトごと渡すか文字列化
        create_log_api_exception(str(exception))

    return JSONResponse(content=result, status_code=status_code)

"""FastAPI用レスポンス作成ヘルパー関数"""
from fastapi.responses import JSONResponse
from typing import Any, Optional
from .create_log import create_log_api_success, create_log_api_error, create_log_api_exception


def create_success_response(status_code: int, response_object: Any) -> JSONResponse:
    """成功レスポンスを作成"""
    result = {'code': 'OK', 'result': response_object}
    create_log_api_success()
    return JSONResponse(content=result, status_code=status_code)


def create_error_response(status_code: int, message: str, exception_message: Optional[Any] = None) -> JSONResponse:
    """エラーレスポンスを作成"""
    result = {'code': 'NG', 'message': message}
    create_log_api_error(message)
    if exception_message is not None:
        create_log_api_exception(exception_message)
    return JSONResponse(content=result, status_code=status_code)

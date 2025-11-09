from rest_framework.response import Response
from .create_log import create_log_api_success
from .create_log import create_log_api_error
from .create_log import create_log_api_exception


def create_success_response(
    status_code: int, response_object: object
) -> Response:
    """_summary_

    Parameters
    ----------
    status_code : int
        _description_
    response_object : object
        _description_
    request : _type_, optional
        _description_, by default None

    Returns
    -------
    Response
        _description_
    """
    result = {
        'code': 'OK',
        'result': response_object
    }
    create_log_api_success()
    return Response(
        data=result,
        status=status_code
    )


def create_error_response(
    status_code: int, message: str, exception_message=None
) -> Response:
    """_summary_
    Parameters
    ----------
    message : str
        エラーメッセージ
    status_code : int
        Rest APIのレスポンスステータスコード

    Returns
    -------
    Response
        django Rest Frameworkのレスポンス
    """
    result = {
        'code': 'NG',
        'message': message
    }
    create_log_api_error(message)
    if (exception_message is not None):
        create_log_api_exception(exception_message)
    return Response(
        data=result,
        status=status_code
    )

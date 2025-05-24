import logging

api_logger = logging.getLogger('api_logger')


def create_log_api_request(request) -> None:
    api_logger.info(
        "API REQUEST",
        extra={'request': request}  # requestオブジェクト全体をログに含める（オプション）
    )


def create_log_api_success(request):
    api_logger.info(
        "API SUCCESS",
        extra={'request': request}
    )


def create_log_api_error(request, message):
    api_logger.error(
        f"ERROR MESSAGE: {message}",
        extra={'request': request}
    )


def create_log_api_exception(exception):
    api_logger.error(
        exception
    )

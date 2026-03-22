import sys
from pathlib import Path

from loguru import logger

# Loguruの設定
logger.remove()  # デフォルトのハンドラを削除
# 標準出力 (コンソール)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | <cyan>{message}</cyan>",
)


class LogManager:
    def __init__(self):
        # クラスの属性として状態を持つ
        self._file_handler_id: int | None = None

    def configure_file_logging(self, log_path: str | Path) -> None:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 既存のハンドラを除去
        if self._file_handler_id is not None:
            logger.remove(self._file_handler_id)

        # 新しいハンドラを追加し、属性を更新
        self._file_handler_id = logger.add(
            log_path.parent / "api_{time:YYYY-MM-DD}.log",
            rotation="10 MB",
            retention="10 days",
            compression="zip",
            level="INFO",
        )


# インスタンス化して使う
log_manager = LogManager()


def log_request(method: str, path: str, query_params: dict) -> None:
    logger.info(f"REQUEST: [{method}] {path} | Params: {query_params}")


def log_success(method: str, path: str, duration: float) -> None:
    logger.info(f"SUCCESS: [{method}] {path} | Time: {duration:.3f}s")


def log_error(
    message: str, error_code: str, exception: Exception | None = None
) -> None:
    if exception is not None:
        logger.error(
            f"ERROR: {error_code} - {message} detail: {str(exception)}"
        )
    else:
        logger.error(f"ERROR: {error_code} - {message} detail: {message}")


def log_exception(exc: Exception) -> None:
    # loguruは .exception() でスタックトレースを綺麗に出してくれる
    logger.exception(f"EXCEPTION OCCURRED: {str(exc)}")

import sys
from pathlib import Path

from loguru import logger

# ログファイルの保存先
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Loguruの設定
logger.remove()  # デフォルトのハンドラを削除
# 標準出力 (コンソール)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
)
# ファイル出力 (ローテーションと保持期間の設定)
logger.add(
    LOG_DIR / "api_{time:YYYY-MM-DD}.log",
    rotation="10 MB",  # 10MBごとに新しいファイルへ
    retention="10 days",  # 10日分保持
    compression="zip",  # 過去ログはzip圧縮
    level="INFO",
)


def log_request(method: str, path: str, query_params: dict) -> None:
    logger.info(f"REQUEST: [{method}] {path} | Params: {query_params}")


def log_success(method: str, path: str, duration: float) -> None:
    logger.info(f"SUCCESS: [{method}] {path} | Time: {duration:.3f}s")


def log_error(message: str, error_code: str) -> None:
    logger.error(f"ERROR: {error_code} - {message}")


def log_exception(exc: Exception) -> None:
    # loguruは .exception() でスタックトレースを綺麗に出してくれる
    logger.exception(f"EXCEPTION OCCURRED: {str(exc)}")

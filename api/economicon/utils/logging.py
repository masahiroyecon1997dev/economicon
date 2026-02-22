import sys
from pathlib import Path

from loguru import logger

# Loguruの設定
logger.remove()  # デフォルトのハンドラを削除
# 標準出力 (コンソール)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
)

# ファイルハンドラのID（後から削除・差し替えできるように保持）
_file_handler_id: int | None = None


def configure_file_logging(log_path: str | Path) -> None:
    """
    ファイルログハンドラを設定する。

    SettingsStore 初期化後に呼び出し、設定ファイルに記載された
    パスへログを出力する。すでに登録済みのファイルハンドラがあれば
    差し替える。

    Args:
        log_path: ログファイルのパス (例: /AppData/Roaming/economicon/logs/app.log)
    """
    global _file_handler_id

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 既存のファイルハンドラを除去
    if _file_handler_id is not None:
        logger.remove(_file_handler_id)

    # ファイル出力 (ローテーションと保持期間の設定)
    _file_handler_id = logger.add(
        log_path.parent / "api_{time:YYYY-MM-DD}.log",
        rotation="10 MB",  # 10 MB ごとに新しいファイルへ
        retention="10 days",  # 10 日分保持
        compression="zip",  # 過去ログは zip 圧縮
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

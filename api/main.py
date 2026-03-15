"""FastAPI メインアプリケーション"""

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi_babel import Babel, BabelConfigs

from economicon.exception_handlers import init_exception_handlers
from economicon.i18n.translation import get_locale_from_settings
from economicon.routers import api_router
from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.data.settings_store import SettingsStore
from economicon.services.data.tables_store import TablesStore
from economicon.utils import log_manager, logger

# ベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent

# Tauri が起動時に確保したポート番号（環境変数 ECONOMICOM_API_PORT で渡される）
_api_port = int(os.environ.get("ECONOMICOM_API_PORT", "8000"))

# Vite 開発サーバー URL（開発時のみ tauri:// と並んで許可する）
_dev_server_url = os.environ.get(
    "VITE_DEV_SERVER_URL", "http://localhost:5173"
)

# 開発モードフラグ（ECONOMICON_DEV_RUN=true のときのみ dev_server_url を許可）
_is_dev_mode = os.environ.get("ECONOMICON_DEV_RUN", "false").lower() == "true"

# 許可するオリジン一覧
# Tauri WebView のみ。開発モード時は Vite dev server も追加
_ALLOW_ORIGINS = [
    "tauri://localhost",  # Windows / Linux の Tauri WebView
    "https://tauri.localhost",  # macOS の Tauri WebView
]
if _is_dev_mode:
    _ALLOW_ORIGINS.append(_dev_server_url)

# Babel設定 - SettingsStoreからロケールを取得する関数を設定
configs = BabelConfigs(
    ROOT_DIR=str(BASE_DIR),
    BABEL_DEFAULT_LOCALE="ja",
    BABEL_TRANSLATION_DIRECTORY="economicon/locales",
)
babel = Babel(configs=configs)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 起動時の処理 ---
    # シングルトンのインスタンスを取得し、初期化を行う
    settings_manager = SettingsStore()
    settings_manager.load_settings()
    log_manager.configure_file_logging(
        settings_manager.get_settings().log_path
    )
    logger.info("SettingsStore has been initialized at startup.")
    tables_store = TablesStore()
    logger.info("TablesStore has been initialized at startup.")

    yield  # ここでアプリがリクエストを待ち受ける
    # --- 終了時の処理 ---
    # 必要に応じてクリーンアップ
    tables_store.clear_tables()
    logger.info("Cleanup TablesStore.")
    analysis_result_store = AnalysisResultStore()
    analysis_result_store.clear_all()
    logger.info("Cleanup AnalysisResultStore (tmp model files deleted.)")
    # import/export でメモリ上に蹜れた設定変更をファイルに一括保存
    try:
        settings_manager.save_settings()
        logger.info("Settings saved on shutdown.")
    except Exception as e:
        logger.warning(f"Failed to save settings on shutdown: {e}")


app = FastAPI(
    title="Economicon App API",
    description="データ分析アプリケーションのAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定（Tauri WebView と開発サーバーのオリジンのみを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# i18nミドルウェア（fastapi-babelが自動的に処理）
@app.middleware("http")
async def combined_middleware(request: Request, call_next):
    # 計測開始
    start_time = time.time()

    # ロケールの設定 - SettingsStoreからロケールを取得してBabelに設定
    locale = get_locale_from_settings()
    # サポートされている言語のみ設定
    if locale not in ["ja", "en"]:
        locale = "ja"
    # Babelのロケールを設定
    babel.locale = locale

    # リクエスト開始ログ
    # pathだけでなく、どの言語でリクエストされたかも残すとデバッグが捗ります
    logger.info(
        f"START: [{request.method}] {request.url.path} (lang: {locale})"
    )

    # メイン処理の実行
    try:
        response = await call_next(request)
    except Exception as e:
        # ここで例外をキャッチすると、エラー時のスタックトレースもログに残せる
        logger.exception(f"Unhandled error occurred: {str(e)}")
        raise e from None

    # 計測終了と完了ログ
    process_time = (time.time() - start_time) * 1000  # ミリ秒変換
    logger.info(
        f"END:   [{request.method}] {request.url.path} | "
        f"Status: {response.status_code} | Time: {process_time:.2f}ms"
    )

    return response


@app.get("/api/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}


# 1. ルーターの登録
app.include_router(api_router, prefix="/api")

# 2. エンドポイントより「後」にハンドラを初期化・登録
init_exception_handlers(app)


# 関数名をそのまま operationId に使うためのロジック
def use_route_names_as_operation_ids(app: FastAPI) -> None:
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = (
                route.name
            )  # Pythonの関数名 (get_settings 等) が入る


use_route_names_as_operation_ids(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=_api_port)

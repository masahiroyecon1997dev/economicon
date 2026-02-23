"""FastAPI メインアプリケーション"""

import os
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from fastapi_babel import Babel, BabelConfigs

from economicon.exception_handlers import init_exception_handlers
from economicon.i18n.translation import get_locale_from_settings
from economicon.routers import api_router
from economicon.services.data.settings_store import SettingsStore
from economicon.services.data.tables_store import TablesStore
from economicon.utils import log_manager, logger

# ベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent
# 静的ファイルのディレクトリ
STATIC_DIR = BASE_DIR / "static"

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

    # ブラウザでアプリを自動的に開く
    url = "http://127.0.0.1:8000"
    dev_run = os.environ.get("economicon_DEV_RUN", "false").lower()
    if dev_run == "false":
        webbrowser.open(url)
    yield  # ここでアプリがリクエストを待ち受ける
    # --- 終了時の処理 ---
    # 必要に応じてクリーンアップ
    tables_store.clear_tables()
    logger.info("Cleanup TablesStore.")


app = FastAPI(
    title="Economicon App API",
    description="データ分析アプリケーションのAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定してください
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


@app.get("/")
async def root():
    """ルートエンドポイント"""
    index_path = STATIC_DIR / "index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # ファイルがない場合はJSONメッセージなどを返す
        return JSONResponse(
            content={"message": ("No index.html found in static folder.")}
        )


@app.get("/health")
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

# フォルダが存在するかチェック
# 存在すればフロントリソースをマウント
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"'{STATIC_DIR}' directory found. Mounted at /static")
else:
    logger.info(f"'{STATIC_DIR}' directory not found. Skipping mount.")
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

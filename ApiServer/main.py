"""FastAPI メインアプリケーション

"""
import logging
import os
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from analysisapp.exception_handlers import init_exception_handlers
from analysisapp.routers import api_router
from analysisapp.services.data.settings_manager import SettingsManager
from analysisapp.services.data.tables_manager import TablesManager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_babel import Babel, BabelConfigs

# ロガーのセットアップ
# "uvicorn.error" を使うと、Uvicornの標準ログと同じ形式で出力されます
logger = logging.getLogger("uvicorn.error")

# ベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent
# 静的ファイルのディレクトリ
STATIC_DIR = BASE_DIR / "static"

# Babel設定
configs = BabelConfigs(
    ROOT_DIR=str(BASE_DIR),
    BABEL_DEFAULT_LOCALE="ja",
    BABEL_TRANSLATION_DIRECTORY="analysisapp/locales",
)
babel = Babel(configs=configs)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 起動時の処理 ---
    # シングルトンのインスタンスを取得し、初期化を行う
    settings_manager = SettingsManager()
    settings_manager.load_settings()
    logger.info("SettingsManager has been initialized at startup.")
    tables_manager = TablesManager()
    logger.info("TablesManager has been initialized at startup.")

    # ブラウザでアプリを自動的に開く
    url = 'http://127.0.0.1:8000'
    dev_run = os.environ.get("ANALYSISAPP_DEV_RUN", "false").lower()
    if dev_run == "false":
        webbrowser.open(url)
    yield  # ここでアプリがリクエストを待ち受ける
    # --- 終了時の処理 ---
    # 必要に応じてクリーンアップ
    tables_manager.clear_tables()
    logger.info("Cleanup TablesManager.")


app = FastAPI(
    title="Analysis App API",
    description="データ分析アプリケーションのAPI",
    version="2.0.0",
    lifespan=lifespan
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
# リクエストのAccept-Languageヘッダーから言語が自動検出されます
@app.middleware("http")
async def babel_middleware(request: Request, call_next):
    """リクエストごとにBabelのロケールを設定"""
    # Accept-Languageヘッダーから言語を取得
    accept_language = request.headers.get("Accept-Language", "ja")
    locale = accept_language.split(",")[0].split("-")[0].split(";")[0]

    # サポートされている言語のみ設定
    if locale not in ['ja', 'en']:
        locale = 'ja'

    # Babelのロケールを設定
    babel.locale = locale

    response = await call_next(request)
    return response


@app.get("/")
async def root():
    """ルートエンドポイント"""
    index_path = STATIC_DIR / "index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # ファイルがない場合はJSONメッセージなどを返す
        return JSONResponse(content={"message": ("No index.html "
                                                 "found in static folder.")})


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}


# 1. ルーターの登録
app.include_router(api_router, prefix="/api")

# 2. エンドポイントより「後」にハンドラを初期化・登録
init_exception_handlers(app)

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

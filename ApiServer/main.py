"""FastAPI メインアプリケーション

"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import webbrowser
import os
import logging
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from analysisapp.exception_handlers import init_exception_handlers
from analysisapp.routers import api_router
from analysisapp.services.data.tables_manager import TablesManager
from analysisapp.services.data.settings_manager import SettingsManager


# i18n サポート
from analysisapp.i18n import set_locale, get_locale

# ロガーのセットアップ
# "uvicorn.error" を使うと、Uvicornの標準ログと同じ形式で出力されます
logger = logging.getLogger("uvicorn.error")

# ベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent

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


# i18nミドルウェア
@app.middleware("http")
async def i18n_middleware(request: Request, call_next):
    """リクエストごとに言語を設定するミドルウェア"""
    # Accept-Languageヘッダーから言語を取得
    accept_language = request.headers.get("Accept-Language", "ja")
    # 最初の言語コードを取得（例: "ja-JP,ja;q=0.9,en;q=0.8" -> "ja"）
    locale = accept_language.split(",")[0].split("-")[0].split(";")[0]
    # サポートされている言語のみ設定（デフォルトは日本語）
    if locale not in ['ja', 'en']:
        locale = 'ja'
    set_locale(locale)

    response = await call_next(request)
    return response


@app.get("/")
async def root():
    """ルートエンドポイント"""
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # ファイルがない場合はJSONメッセージなどを返す
        return JSONResponse(content={"message": "No index.html found in static folder."})


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}


# 1. ルーターの登録
app.include_router(api_router, prefix="/api")

# 2. エンドポイントより「後」にハンドラを初期化・登録
init_exception_handlers(app)

# フォルダが存在するかチェック
static_dir = "static"
# 存在すればフロントリソースをマウント
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir), name="static")
    logger.info(f"'{static_dir}' directory found. Mounted at /static")
else:
    logger.info(f"'{static_dir}' directory not found. Skipping mount.")

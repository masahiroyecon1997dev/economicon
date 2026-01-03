"""FastAPI メインアプリケーション

"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from analysisapp.exception_handlers import init_exception_handlers
from analysisapp.routers import api_router
from analysisapp.services.data.tables_manager import TablesManager
from analysisapp.services.data.settings_manager import SettingsManager


# i18n サポート
from analysisapp.i18n import set_locale, get_locale

# ベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 起動時の処理 ---
    # シングルトンのインスタンスを取得し、初期化を行う
    settings_manager = SettingsManager()
    settings_manager.load_settings()
    print("SettingsManager has been initialized at startup.")
    tables_manager = TablesManager()
    print("TablesManager has been initialized at startup.")

    yield  # ここでアプリがリクエストを待ち受ける

    # --- 終了時の処理 ---
    # 必要に応じてクリーンアップ

    tables_manager.clear_tables()
    print("Cleanup TablesManager.")


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
    return {"message": "Analysis App API", "version": "2.0.0", "locale": get_locale()}


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}


# 1. ルーターの登録
app.include_router(api_router, prefix="/api")

# 2. エンドポイントより「後」にハンドラを初期化・登録
init_exception_handlers(app)

"""FastAPI メインアプリケーション

"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

# i18n サポート
from analysisapp.api.i18n import set_locale, get_locale

# ベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Analysis App API",
    description="データ分析アプリケーションのAPI",
    version="2.0.0"
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


# ルーターのインポートと登録
from analysisapp.api.routers import add_column

app.include_router(add_column.router, prefix="/api", tags=["column"])

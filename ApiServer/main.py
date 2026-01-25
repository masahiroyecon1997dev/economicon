"""FastAPI メインアプリケーション

"""
import logging
import os
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from analysisapp.exception_handlers import init_exception_handlers
from analysisapp.i18n.translation import get_locale_from_settings, gettext as _
from analysisapp.routers import api_router
from analysisapp.services.data.settings_manager import SettingsManager
from analysisapp.services.data.tables_store import TablesStore
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
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

# Babel設定 - SettingsManagerからロケールを取得する関数を設定
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
    tables_store = TablesStore()
    logger.info("TablesStore has been initialized at startup.")

    # ブラウザでアプリを自動的に開く
    url = 'http://127.0.0.1:8000'
    dev_run = os.environ.get("ANALYSISAPP_DEV_RUN", "false").lower()
    if dev_run == "false":
        webbrowser.open(url)
    yield  # ここでアプリがリクエストを待ち受ける
    # --- 終了時の処理 ---
    # 必要に応じてクリーンアップ
    tables_store.clear_tables()
    logger.info("Cleanup TablesStore.")


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
@app.middleware("http")
async def babel_middleware(request: Request, call_next):
    """settingsManagerのロケールを設定"""
    locale = get_locale_from_settings()

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """
    Pydantic バリデーションエラーハンドラ

    422 エラーのメッセージを多言語化します。
    """
    errors = exc.errors()
    translated_errors = []

    for error in errors:
        translated_error = error.copy()

        # エラータイプに基づく翻訳
        error_type = error.get("type", "")
        error_msg = error.get("msg", "")

        # エラータイプごとの翻訳キーマッピング
        type_translation_map = {
            "missing": "ValidationError.FieldRequired",
            "string_type": "ValidationError.StringTypeExpected",
            "int_type": "ValidationError.IntTypeExpected",
            "float_type": "ValidationError.FloatTypeExpected",
            "bool_type": "ValidationError.BoolTypeExpected",
            "list_type": "ValidationError.ListTypeExpected",
            "dict_type": "ValidationError.DictTypeExpected",
            "value_error": "ValidationError.ValueError",
            "type_error": "ValidationError.TypeError",
            "assertion_error": "ValidationError.AssertionError",
            "less_than": "ValidationError.LessThan",
            "less_than_equal": "ValidationError.LessThanEqual",
            "greater_than": "ValidationError.GreaterThan",
            "greater_than_equal": "ValidationError.GreaterThanEqual",
            "string_too_short": "ValidationError.StringTooShort",
            "string_too_long": "ValidationError.StringTooLong",
            "enum": "ValidationError.InvalidEnum",
            "literal_error": "ValidationError.LiteralError",
        }

        # エラータイプに対応する翻訳キーがあれば使用
        if error_type in type_translation_map:
            translation_key = type_translation_map[error_type]
            translated_msg = _(translation_key)

            # 翻訳が見つからない場合（キーがそのまま返る）は
            # 元のメッセージを翻訳
            if translated_msg == translation_key:
                translated_msg = _(error_msg)
        else:
            # マッピングにない場合は直接メッセージを翻訳
            translated_msg = _(error_msg)

        translated_error["msg"] = translated_msg
        translated_errors.append(translated_error)

    return JSONResponse(
        status_code=422,
        content={"detail": translated_errors}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    # ロジックで発生した ValueError を 400 Bad Request としてフロントに返す
    return JSONResponse(
        status_code=400,
        content={
            'code': 'NG',
            'message': str(exc)
        }
    )


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

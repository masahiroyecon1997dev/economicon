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

    422 エラーのメッセージを多言語化し、ユーザーフレンドリーな
    メッセージを生成します。
    """
    errors = exc.errors()
    translated_messages = []

    for error in errors:
        # フィールド名を取得（loc の最後の要素）
        loc = error.get("loc", ())
        field_name = loc[-1] if loc else ""

        # フィールド名を翻訳（messages.po に定義）
        translated_field = _(f"Field.{field_name}")
        if translated_field == f"Field.{field_name}":
            # 翻訳が見つからない場合はそのまま使用
            translated_field = field_name

        # エラータイプとコンテキストを取得
        error_type = error.get("type", "")
        ctx = error.get("ctx", {})

        # エラータイプに応じてメッセージを構築
        if error_type == "missing":
            message = _("{field} は必須です").format(
                field=translated_field
            )

        elif error_type == "string_type":
            message = _("{field} は文字列である必要があります").format(
                field=translated_field
            )

        elif error_type == "int_type":
            message = _("{field} は整数である必要があります").format(
                field=translated_field
            )

        elif error_type == "float_type":
            message = _("{field} は数値である必要があります").format(
                field=translated_field
            )

        elif error_type == "bool_type":
            message = _("{field} は真偽値である必要があります").format(
                field=translated_field
            )

        elif error_type == "list_type":
            message = _("{field} はリストである必要があります").format(
                field=translated_field
            )

        elif error_type == "dict_type":
            message = _("{field} は辞書である必要があります").format(
                field=translated_field
            )

        elif error_type == "string_too_short":
            min_length = ctx.get("min_length", "")
            message = _(
                "{field} は{min_length}文字以上である必要があります"
            ).format(
                field=translated_field,
                min_length=min_length
            )

        elif error_type == "string_too_long":
            max_length = ctx.get("max_length", "")
            message = _(
                "{field} は{max_length}文字以下である必要があります"
            ).format(
                field=translated_field,
                max_length=max_length
            )

        elif error_type == "less_than":
            limit = ctx.get("lt", "")
            message = _("{field} は{limit}未満である必要があります").format(
                field=translated_field,
                limit=limit
            )

        elif error_type == "less_than_equal":
            limit = ctx.get("le", "")
            message = _("{field} は{limit}以下である必要があります").format(
                field=translated_field,
                limit=limit
            )

        elif error_type == "greater_than":
            limit = ctx.get("gt", "")
            message = _("{field} は{limit}より大きい必要があります").format(
                field=translated_field,
                limit=limit
            )

        elif error_type == "greater_than_equal":
            limit = ctx.get("ge", "")
            message = _("{field} は{limit}以上である必要があります").format(
                field=translated_field,
                limit=limit
            )

        elif error_type in ("literal_error", "enum"):
            expected = ctx.get("expected", "")
            if expected:
                message = _(
                    "{field} は次のいずれかである必要があります: {expected}"
                ).format(
                    field=translated_field,
                    expected=expected
                )
            else:
                message = _("{field} の値が無効です").format(
                    field=translated_field
                )

        else:
            # その他のエラータイプは元のメッセージを翻訳
            original_msg = error.get("msg", "")
            translated_msg = _(original_msg)
            if translated_field and translated_field != field_name:
                message = f"{translated_field}: {translated_msg}"
            else:
                message = translated_msg

        translated_messages.append(message)

    return JSONResponse(
        status_code=422,
        content={
            'code': 'NG',
            'message': translated_messages
        }
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

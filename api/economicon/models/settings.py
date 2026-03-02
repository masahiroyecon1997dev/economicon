"""設定関連のスキーマ定義"""

from typing import Annotated

from pydantic import Field

from economicon.models.common import BaseRequest, BaseResult

# ---------------------------------------------------------------------------
# 共通フィールド基底
# ---------------------------------------------------------------------------


class AppSettings(BaseResult):
    """アプリケーション設定フィールドの共通モデル"""

    language: Annotated[
        str,
        Field(
            title="Language",
            description="アプリケーションの表示言語（ja: 日本語, en: 英語）",
        ),
    ]
    last_opened_path: Annotated[
        str,
        Field(
            title="Last Opened Path",
            description="最後に開いたフォルダパス",
        ),
    ]
    theme: Annotated[
        str,
        Field(
            title="Theme",
            description="アプリケーションのテーマ（light / dark）",
        ),
    ]
    encoding: Annotated[
        str,
        Field(
            title="Encoding",
            description="ファイルエンコーディング",
        ),
    ]
    log_path: Annotated[
        str,
        Field(
            title="Log Path",
            description="ログファイルの出力先パス",
        ),
    ]


# ---------------------------------------------------------------------------
# 設定取得
# ---------------------------------------------------------------------------


class GetSettingsRequestBody(BaseRequest):
    """アプリケーション設定取得リクエスト（パラメータなし）"""

    pass


class GetSettingsResult(AppSettings):
    """アプリケーション設定取得レスポンス"""


# ---------------------------------------------------------------------------
# 設定更新
# ---------------------------------------------------------------------------


class UpdateSettingsRequest(BaseRequest):
    """アプリケーション設定更新リクエスト（すべてのフィールドが省略可能）"""

    language: Annotated[
        str | None,
        Field(
            default=None,
            title="Language",
            description="表示言語。'ja' または 'en' のみ許可。",
            pattern=r"^(ja|en)$",
        ),
    ] = None
    theme: Annotated[
        str | None,
        Field(
            default=None,
            title="Theme",
            description="テーマ。'light' または 'dark' のみ許可。",
            pattern=r"^(light|dark)$",
        ),
    ] = None
    encoding: Annotated[
        str | None,
        Field(
            default=None,
            title="Encoding",
            description="ファイルエンコーディング",
        ),
    ] = None
    log_path: Annotated[
        str | None,
        Field(
            default=None,
            title="Log Path",
            description="ログファイルの出力先パス",
        ),
    ] = None


class UpdateSettingsResult(AppSettings):
    """アプリケーション設定更新レスポンス（更新後の全設定を返す）"""

"""設定関連のスキーマ定義"""

from typing import Annotated

from pydantic import Field

from economicon.models.common import BaseRequest, BaseResult


class GetSettingsRequestBody(BaseRequest):
    """アプリケーション設定取得リクエスト（パラメータなし）"""

    pass


class GetSettingsResult(BaseResult):
    """アプリケーション設定取得レスポンス"""

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

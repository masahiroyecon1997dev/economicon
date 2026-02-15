"""設定関連のスキーマ定義"""

from pydantic import BaseModel


class GetSettingsRequestBody(BaseModel):
    """アプリケーション設定取得リクエスト（パラメータなし）"""

    pass

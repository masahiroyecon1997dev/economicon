"""ファイル操作・取得関連のスキーマ定義"""
from pydantic import BaseModel, Field


class GetFilesRequest(BaseModel):
    """ファイル一覧取得リクエスト（GETクエリパラメータ用）"""
    directoryPath: str = Field(..., description="対象ディレクトリパス")

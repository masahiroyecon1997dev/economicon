"""ファイル操作・取得関連のスキーマ定義"""
from pydantic import BaseModel, ConfigDict, Field


class GetFilesRequest(BaseModel):
    """ファイル一覧取得リクエスト"""
    directory_path: str = Field(
        ...,
        alias="directoryPath",
        description="対象ディレクトリパス",
        min_length=1,
        max_length=1024
    )

    model_config = ConfigDict(populate_by_name=True)

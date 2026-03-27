"""シャットダウン関連のスキーマ定義"""

from typing import Annotated

from pydantic import Field

from economicon.schemas.common import BaseResult


class ShutdownResult(BaseResult):
    """アプリ終了前クリーンアップの結果モデル"""

    status: Annotated[
        str,
        Field(
            title="Status",
            description="クリーンアップ処理のステータス（ok）",
        ),
    ]

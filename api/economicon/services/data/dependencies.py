from typing import Annotated

from fastapi import Depends

from .tables_store import TablesStore


def get_tables_store() -> TablesStore:
    """TablesStore シングルトンを返す DI プロバイダ"""
    return TablesStore()


# ルーターで型アノテーションとして使い回す型エイリアス
TablesStoreDep = Annotated[TablesStore, Depends(get_tables_store)]

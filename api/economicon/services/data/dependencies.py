from typing import Annotated

from fastapi import Depends

from .analysis_result_store import AnalysisResultStore
from .settings_store import SettingsStore
from .tables_store import TablesStore


def get_tables_store() -> TablesStore:
    """TablesStore シングルトンを返す DI プロバイダ"""
    return TablesStore()


def get_analysis_result_store() -> AnalysisResultStore:
    """AnalysisResultStore シングルトンを返す DI プロバイダ"""
    return AnalysisResultStore()


def get_settings_store() -> SettingsStore:
    """SettingsStore シングルトンを返す DI プロバイダ"""
    return SettingsStore()


# ルーターで型アノテーションとして使い回す型エイリアス
TablesStoreDep = Annotated[TablesStore, Depends(get_tables_store)]
AnalysisResultStoreDep = Annotated[
    AnalysisResultStore, Depends(get_analysis_result_store)
]
SettingsStoreDep = Annotated[SettingsStore, Depends(get_settings_store)]

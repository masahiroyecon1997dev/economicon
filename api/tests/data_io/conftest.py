"""data_io テストの共通フィクスチャ"""

import pytest

from economicon.services.data.settings_store import SettingsStore


@pytest.fixture
def settings_store():
    """SettingsStore のフィクスチャ

    設定を初期化（または再読み込み）してシングルトンを返す。
    インポート成功後の last_opened_path 更新検証に使用する。
    """
    store = SettingsStore()
    store.load_settings()
    return store

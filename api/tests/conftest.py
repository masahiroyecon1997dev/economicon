"""テスト全体の共通フィクスチャと設定。

pytest が収集するテストファイルより先にこの conftest.py が読み込まれるため、
ここで FastAPI の認証依存関係をバイパスする。
これにより既存のテストを変更することなく auth レイヤーを導入できる。
"""

import os

import pytest

from economicon.core.auth import get_app_settings, verify_token
from main import app

# テスト用トークンを環境変数に設定する。
# AppSettings の lru_cache より前にセットするため、
# モジュールインポートより先にここで定義する必要がある。
TEST_AUTH_TOKEN = "test-auth-token-for-pytest"
os.environ["ECONOMICOM_API_AUTH_TOKEN"] = TEST_AUTH_TOKEN


@pytest.fixture(autouse=True, scope="session")
def override_auth():
    """セッション全体で認証依存関係をバイパスする。

    各テストファイルが独自の ``client`` フィクスチャを持つため、
    ヘッダーを注入する代わりに FastAPI の dependency_overrides で
    ``verify_token`` を no-op 関数に差し替える。
    これにより既存テストを一切変更せずに済む。
    """
    # cache をリセットして TEST_AUTH_TOKEN を確実に読み込ませる
    get_app_settings.cache_clear()

    def _no_op_verify():
        """テスト環境では認証チェックをスキップする"""
        return None

    app.dependency_overrides[verify_token] = _no_op_verify
    yield
    # テスト終了後はオーバーライドをクリアする
    app.dependency_overrides.clear()

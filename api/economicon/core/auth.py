"""Tauri 起動時に環境変数経由で渡される認証トークンの検証モジュール。

Tauri は起動時に UUID v4 トークンを生成し、環境変数
``ECONOMICOM_API_AUTH_TOKEN`` としてサイドカープロセスに引き渡す。
全 API エンドポイントは、リクエストヘッダー ``X-Auth-Token`` を通じて
このトークンを提示しなければならない。
"""

from functools import cache

from fastapi import Header, HTTPException, status
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """環境変数から認証トークンを読み込む設定クラス。

    Tauri が起動時に ``ECONOMICOM_API_AUTH_TOKEN`` を設定するため、
    サイドカーとして起動された FastAPI は自動的にこの値を取得できる。
    """

    model_config = SettingsConfigDict(
        # 大文字・小文字を区別しない（環境変数は一般的に大文字）
        case_sensitive=False,
    )

    economicom_api_auth_token: str = ""


@cache
def get_app_settings() -> AppSettings:
    """AppSettings のシングルトンを返す。

    cache により、初回呼び出し時のみインスタンス化される。
    pytest では conftest.py で環境変数を設定してから
    ``get_app_settings.cache_clear()`` を呼ぶことでリセット可能。
    """
    return AppSettings()


def verify_token(
    x_auth_token: str = Header(
        ...,
        alias="X-Auth-Token",
        description="Tauri 起動時に生成された認証トークン",
    ),
) -> None:
    """全リクエストに対して ``X-Auth-Token`` ヘッダーを検証する依存関数。

    Args:
        x_auth_token: リクエストヘッダー ``X-Auth-Token`` の値。

    Raises:
        HTTPException: トークンが一致しない場合、または
            環境変数が未設定の場合に 401 を返す。
    """
    expected = get_app_settings().economicom_api_auth_token

    # 環境変数が未設定の場合はサーバー設定ミスとして拒否する
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth token is not configured on the server.",
        )

    if x_auth_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Auth-Token header.",
        )

import os

from economicon.services.data.settings_store import SettingsStore
from economicon.utils import logger


def update_last_opened_path(
    settings_store: SettingsStore, path: str
) -> None:
    """last_opened_path をメモリ上の設定に反映する。"""
    try:
        normalized = path.replace(os.sep, "/")
        settings_store.update_settings(last_opened_path=normalized)
        logger.info(f"Updated last_opened_path: {normalized}")
    except Exception as exc:
        logger.warning(
            f"Failed to update last_opened_path in settings: {exc}"
        )

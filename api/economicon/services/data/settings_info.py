"""
設定情報を保持するデータクラス
"""


class SettingsInfo:
    """
    アプリケーション設定情報を保持するデータクラス
    """

    _language: str
    _last_opened_path: str
    _theme: str
    _encoding: str
    _log_path: str

    def __init__(  # noqa: PLR0913
        self,
        language: str,
        last_opened_path: str,
        theme: str,
        encoding: str,
        log_path: str,
    ):
        self._language = language
        self._last_opened_path = last_opened_path
        self._theme = theme
        self._encoding = encoding
        self._log_path = log_path

    @property
    def language(self) -> str:
        return self._language

    @property
    def last_opened_path(self) -> str:
        return self._last_opened_path

    @property
    def theme(self) -> str:
        return self._theme

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def log_path(self) -> str:
        return self._log_path

    def to_dict(self) -> dict:
        """
        設定情報を辞書形式で返す

        Returns:
            dict: キャメルケースのキーで設定情報を含む辞書
        """
        return {
            "language": self._language,
            "lastOpenedPath": self._last_opened_path,
            "theme": self._theme,
            "encoding": self._encoding,
            "logPath": self._log_path,
        }

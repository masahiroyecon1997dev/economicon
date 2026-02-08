"""
設定情報を保持するデータクラス
"""


class SettingsInfo:
    """
    アプリケーション設定情報を保持するデータクラス
    """
    _os_name: str
    _default_folder_path: str
    _display_rows: int
    _app_language: str
    _encoding: str
    _path_separator: str

    def __init__(
        self,
        os_name: str,
        default_folder_path: str,
        display_rows: int,
        app_language: str,
        encoding: str,
        path_separator: str
    ):
        self._os_name = os_name
        self._default_folder_path = default_folder_path
        self._display_rows = display_rows
        self._app_language = app_language
        self._encoding = encoding
        self._path_separator = path_separator

    @property
    def os_name(self) -> str:
        return self._os_name

    @property
    def default_folder_path(self) -> str:
        return self._default_folder_path

    @property
    def display_rows(self) -> int:
        return self._display_rows

    @property
    def app_language(self) -> str:
        return self._app_language

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def path_separator(self) -> str:
        return self._path_separator

    def to_dict(self) -> dict:
        """
        設定情報を辞書形式で返す

        Returns:
            dict: キャメルケースのキーで設定情報を含む辞書
        """
        return {
            'osName': self._os_name,
            'defaultFolderPath': self._default_folder_path,
            'displayRows': self._display_rows,
            'appLanguage': self._app_language,
            'encoding': self._encoding,
            'pathSeparator': self._path_separator
        }

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        """
        アプリケーション起動時に実行される処理

        設定ファイルを読み込み、SettingsManagerを初期化します。
        """
        from .apis.data.settings_manager import SettingsManager

        # 設定の初期化
        settings_manager = SettingsManager()
        settings_manager.load_settings()
        print("Application settings loaded successfully.")

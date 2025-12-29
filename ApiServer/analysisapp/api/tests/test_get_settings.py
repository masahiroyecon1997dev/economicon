from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.settings_manager import SettingsManager


class TestApiGetSettings(APITestCase):
    def setUp(self):
        # 設定マネージャーが初期化されていることを確認
        self.settings_manager = SettingsManager()

    def test_get_settings_success(self):
        # 正常系テスト: 設定情報を取得
        response = self.client.get(
            '/api/get-settings',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # 必須フィールドの存在確認
        result = response_data['result']
        self.assertIn('osName', result)
        self.assertIn('defaultFolderPath', result)
        self.assertIn('displayRows', result)
        self.assertIn('appLanguage', result)
        self.assertIn('encoding', result)
        self.assertIn('pathSeparator', result)

        # デフォルト値の確認
        self.assertEqual(result['displayRows'], 100)
        self.assertEqual(result['appLanguage'], 'ja')
        self.assertEqual(result['encoding'], 'utf-8')
        self.assertEqual(result['pathSeparator'], '/')

    def test_settings_manager_singleton(self):
        # シングルトンパターンのテスト
        manager1 = SettingsManager()
        manager2 = SettingsManager()
        self.assertIs(manager1, manager2)

    def test_settings_info_properties(self):
        # 設定情報のプロパティアクセステスト
        settings_info = self.settings_manager.get_settings()

        # プロパティが正しく取得できることを確認
        self.assertIsNotNone(settings_info.os_name)
        self.assertIsNotNone(settings_info.default_folder_path)
        self.assertEqual(settings_info.display_rows, 100)
        self.assertEqual(settings_info.app_language, 'ja')
        self.assertEqual(settings_info.encoding, 'utf-8')
        self.assertEqual(settings_info.path_separator, '/')

    def test_settings_info_to_dict(self):
        # to_dict()メソッドのテスト
        settings_info = self.settings_manager.get_settings()
        settings_dict = settings_info.to_dict()

        # キャメルケースのキーが存在することを確認
        self.assertIn('osName', settings_dict)
        self.assertIn('defaultFolderPath', settings_dict)
        self.assertIn('displayRows', settings_dict)
        self.assertIn('appLanguage', settings_dict)
        self.assertIn('encoding', settings_dict)
        self.assertIn('pathSeparator', settings_dict)

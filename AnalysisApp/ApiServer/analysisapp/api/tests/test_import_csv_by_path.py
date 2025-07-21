from rest_framework.test import APITestCase
from rest_framework import status
import json
import polars as pl
import tempfile
import os
from ..apis.data.tables_manager import TablesManager


class TestApiImportCsvByPath(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()

        # テスト用のCSVファイルパス
        self.test_csv_comma = '/AnalysisApp/AnalysisApp/SampleData'\
                              '/TestDataComma.csv'
        self.test_csv_tab = '/AnalysisApp/AnalysisApp/SampleData'\
                            '/TestDataTab1.tsv'
        self.empty_csv = '/AnalysisApp/AnalysisApp/SampleData'\
                         '/Empty.csv'

    def test_import_csv_by_path_comma_separator(self):
        """
        カンマ区切りのCSVファイルをパス指定でインポートするテスト
        """
        # 期待データをPolarsで読み込み
        expected_data = pl.read_csv(self.test_csv_comma, encoding='utf8')

        # APIリクエスト
        request_data = {
            'filePath': self.test_csv_comma,
            'tableName': 'TestCommaTable',
            'separator': ','
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestCommaTable',
                         response_data['result']['tableName'])

        # データの検証
        df = self.tables_manager.get_table('TestCommaTable').table
        self.assertEqual(True, expected_data.equals(df))

    def test_import_csv_by_path_tab_separator(self):
        """
        タブ区切りのファイルをCSVとしてパス指定でインポートするテスト
        """
        # 期待データをPolarsで読み込み
        expected_data = pl.read_csv(self.test_csv_tab, separator='\t',
                                    encoding='utf8')

        # APIリクエスト
        request_data = {
            'filePath': self.test_csv_tab,
            'tableName': 'TestTabTable',
            'separator': '\t'
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestTabTable', response_data['result']['tableName'])

        # データの検証
        df = self.tables_manager.get_table('TestTabTable').table
        self.assertEqual(True, expected_data.equals(df))

    def test_import_csv_by_path_custom_separator(self):
        """
        セミコロン区切りのCSVファイルのテスト（テストファイルを作成）
        """
        # 一時的なセミコロン区切りファイルを作成
        temp_data = "col1;col2;col3\n1;2;3\n4;5;6\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv',
                                         delete=False) as f:
            f.write(temp_data)
            temp_path = f.name

        try:
            # APIリクエスト
            request_data = {
                'filePath': temp_path,
                'tableName': 'TestSemicolonTable',
                'separator': ';'
            }
            response = self.client.post('/api/import-csv-by-path',
                                        data=json.dumps(request_data),
                                        content_type='application/json')

            response_data = response.json()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual('OK', response_data['code'])
            self.assertEqual('TestSemicolonTable',
                             response_data['result']['tableName'])

            # データの検証
            df = self.tables_manager.get_table('TestSemicolonTable').table
            self.assertEqual(3, len(df.columns))  # 3列
            self.assertEqual(2, len(df))  # 2行（ヘッダー除く）
        finally:
            # 一時ファイルを削除
            os.unlink(temp_path)

    def test_import_csv_by_path_default_separator(self):
        """
        separatorパラメータを省略した場合のテスト（デフォルトはカンマ）
        """
        # 期待データをPolarsで読み込み
        expected_data = pl.read_csv(self.test_csv_comma, encoding='utf8')

        # APIリクエスト（separatorを省略）
        request_data = {
            'filePath': self.test_csv_comma,
            'tableName': 'TestDefaultSeparator'
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestDefaultSeparator',
                         response_data['result']['tableName'])

        # データの検証
        df = self.tables_manager.get_table('TestDefaultSeparator').table
        self.assertEqual(True, expected_data.equals(df))

    def test_import_csv_by_path_file_not_exists(self):
        """
        存在しないファイルパスを指定した場合のテスト
        """
        request_data = {
            'filePath': '/non/existent/file.csv',
            'tableName': 'TestNonExistent',
            'separator': ','
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("filePath does not exist: /non/existent/file.csv",
                      response_data['message'])

    def test_import_csv_by_path_invalid_file_extension(self):
        """
        CSV以外のファイル拡張子を指定した場合のテスト
        """
        request_data = {
            'filePath': '/AnalysisApp/AnalysisApp'
                        '/SampleData/TestDataXlsx.xlsx',
            'tableName': 'TestInvalidExtension',
            'separator': ','
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Failed to parse CSV file: Invalid format or encoding.",
                      response_data['message'])

    def test_import_csv_by_path_missing_file_path(self):
        """
        filePathパラメータが未指定の場合のテスト
        """
        request_data = {
            'tableName': 'TestMissingPath',
            'separator': ','
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("filePath is required", response_data['message'])

    def test_import_csv_by_path_missing_table_name(self):
        """
        tableNameパラメータが未指定の場合のテスト
        """
        request_data = {
            'filePath': self.test_csv_comma,
            'separator': ','
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("tableName is required.", response_data['message'])

    def test_import_csv_by_path_duplicate_table_name(self):
        """
        既存のテーブル名と重複する場合のテスト
        """
        # 先にテーブルを作成
        first_request_data = {
            'filePath': self.test_csv_comma,
            'tableName': 'DuplicateTable',
            'separator': ','
        }
        self.client.post('/api/import-csv-by-path',
                         data=json.dumps(first_request_data),
                         content_type='application/json')

        # 同じテーブル名で再度作成を試行
        second_request_data = {
            'filePath': self.test_csv_comma,
            'tableName': 'DuplicateTable',
            'separator': ','
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(second_request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        # テーブル名重複エラーメッセージを確認

    def test_import_csv_by_path_empty_separator(self):
        """
        空の区切り文字を指定した場合のテスト
        """
        request_data = {
            'filePath': self.test_csv_comma,
            'tableName': 'TestEmptySeparator',
            'separator': ''
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("separator must be at least 1 characters long.",
                      response_data['message'])

    def test_import_csv_by_path_invalid_json(self):
        """
        不正なJSONを送信した場合のテスト
        """
        response = self.client.post('/api/import-csv-by-path',
                                    data='invalid json',
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Invalid JSON format", response_data['message'])

    def test_import_csv_by_path_malformed_csv(self):
        """
        不正な形式のCSVファイルを指定した場合のテスト
        """
        # エラーCSVファイルが存在する場合
        request_data = {
            'filePath': '/AnalysisApp/AnalysisApp/SampleData/Error.csv',
            'tableName': 'TestMalformed',
            'separator': ','
        }
        response = self.client.post('/api/import-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Failed to parse CSV file: Invalid format or encoding.",
                      response_data['message'])

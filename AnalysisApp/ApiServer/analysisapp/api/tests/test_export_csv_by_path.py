from rest_framework.test import APITestCase
from rest_framework import status
import json
import polars as pl
import tempfile
import os
from ..apis.data.tables_manager import TablesManager


class TestApiExportCsvByPath(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()

        # テスト用のテーブルデータを作成
        self.test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        self.tables_manager.store_table('TestTable', self.test_data)

        # テスト用の出力ディレクトリ
        self.test_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        import shutil
        shutil.rmtree(self.test_output_dir, ignore_errors=True)

    def test_export_csv_by_path_default_separator(self):
        """
        デフォルトのカンマ区切りでCSVファイルをエクスポートするテスト
        """
        output_path = os.path.join(self.test_output_dir, 'test_output.csv')
        
        # APIリクエスト
        request_data = {
            'tableName': 'TestTable',
            'filePath': output_path
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたCSVファイルの内容を検証
        exported_data = pl.read_csv(output_path)
        self.assertEqual(True, self.test_data.equals(exported_data))

    def test_export_csv_by_path_custom_separator(self):
        """
        タブ区切りでCSVファイルをエクスポートするテスト
        """
        output_path = os.path.join(self.test_output_dir, 'test_output_tab.csv')
        
        # APIリクエスト
        request_data = {
            'tableName': 'TestTable',
            'filePath': output_path,
            'separator': '\t'
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたCSVファイルの内容を検証（タブ区切り）
        exported_data = pl.read_csv(output_path, separator='\t')
        self.assertEqual(True, self.test_data.equals(exported_data))

    def test_export_csv_by_path_semicolon_separator(self):
        """
        セミコロン区切りでCSVファイルをエクスポートするテスト
        """
        output_path = os.path.join(self.test_output_dir, 'test_output_semicolon.csv')
        
        # APIリクエスト
        request_data = {
            'tableName': 'TestTable',
            'filePath': output_path,
            'separator': ';'
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたCSVファイルの内容を検証（セミコロン区切り）
        exported_data = pl.read_csv(output_path, separator=';')
        self.assertEqual(True, self.test_data.equals(exported_data))

    def test_export_csv_by_path_table_not_exists(self):
        """
        存在しないテーブル名を指定した場合のテスト
        """
        output_path = os.path.join(self.test_output_dir, 'test_output.csv')
        
        request_data = {
            'tableName': 'NonExistentTable',
            'filePath': output_path
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("tableName 'NonExistentTable' does not exist", 
                      response_data['message'])

    def test_export_csv_by_path_invalid_output_directory(self):
        """
        存在しない出力ディレクトリを指定した場合のテスト
        """
        output_path = '/non/existent/directory/test_output.csv'
        
        request_data = {
            'tableName': 'TestTable',
            'filePath': output_path
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Output directory does not exist", response_data['message'])

    def test_export_csv_by_path_missing_table_name(self):
        """
        tableNameパラメータが未指定の場合のテスト
        """
        output_path = os.path.join(self.test_output_dir, 'test_output.csv')
        
        request_data = {
            'filePath': output_path
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("tableName is required", response_data['message'])

    def test_export_csv_by_path_missing_file_path(self):
        """
        filePathパラメータが未指定の場合のテスト
        """
        request_data = {
            'tableName': 'TestTable'
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("filePath is required", response_data['message'])

    def test_export_csv_by_path_empty_separator(self):
        """
        空の区切り文字を指定した場合のテスト
        """
        output_path = os.path.join(self.test_output_dir, 'test_output.csv')
        
        request_data = {
            'tableName': 'TestTable',
            'filePath': output_path,
            'separator': ''
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("separator must be at least 1 characters long", 
                      response_data['message'])

    def test_export_csv_by_path_invalid_json(self):
        """
        不正なJSONを送信した場合のテスト
        """
        response = self.client.post('/api/export-csv-by-path',
                                    data='invalid json',
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Invalid JSON format", response_data['message'])

    def test_export_csv_by_path_empty_table(self):
        """
        空のテーブルをエクスポートする場合のテスト
        """
        # 空のテーブルを作成
        empty_data = pl.DataFrame({'col1': [], 'col2': []})
        self.tables_manager.store_table('EmptyTable', empty_data)
        
        output_path = os.path.join(self.test_output_dir, 'empty_output.csv')
        
        request_data = {
            'tableName': 'EmptyTable',
            'filePath': output_path
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたCSVファイルの内容を検証（空のデータ）
        exported_data = pl.read_csv(output_path)
        self.assertEqual(True, empty_data.equals(exported_data))

    def test_export_csv_by_path_large_table(self):
        """
        大きなテーブルをエクスポートする場合のテスト
        """
        # 大きなテーブルを作成
        large_data = pl.DataFrame({
            'id': list(range(1000)),
            'value': [f'value_{i}' for i in range(1000)],
            'number': [i * 1.5 for i in range(1000)]
        })
        self.tables_manager.store_table('LargeTable', large_data)
        
        output_path = os.path.join(self.test_output_dir, 'large_output.csv')
        
        request_data = {
            'tableName': 'LargeTable',
            'filePath': output_path
        }
        response = self.client.post('/api/export-csv-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたCSVファイルの内容を検証
        exported_data = pl.read_csv(output_path)
        self.assertEqual(True, large_data.equals(exported_data))
        self.assertEqual(1000, len(exported_data))  # 行数確認
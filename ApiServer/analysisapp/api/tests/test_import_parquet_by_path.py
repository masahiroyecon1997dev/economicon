import json
import os
import shutil
import tempfile

import numpy as np
import polars as pl
from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestApiImportParquetByPath(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テスト用の出力ディレクトリ
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_import_parquet_by_path_simple(self):
        """
        シンプルなPARQUETファイルをパス指定でインポートするテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_parquet(
            f'{self.test_dir}/TestData.parquet')

        # APIリクエスト
        request_data = {
            'filePath': f'{self.test_dir}/TestData.parquet',
            'tableName': 'TestSimpleParquet'
        }
        response = self.client.post('/api/import-parquet-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestSimpleParquet',
                         response_data['result']['tableName'])

        # データの検証
        df = self.tables_manager.get_table('TestSimpleParquet').table
        self.assertEqual(True, test_data.equals(df))

    def test_import_parquet_by_path_large_data(self):
        """
        大きなPARQUETファイルをパス指定でインポートするテスト
        """
        N_ROWS = 5000
        N_COLS = 500
        rng = np.random.default_rng(42)
        data = rng.integers(0, 100, size=(N_ROWS, N_COLS), dtype=np.int32)
        column_names = [f"col_{i}" for i in range(N_COLS)]
        df_sample = pl.DataFrame(
            data,
            schema=column_names
        )
        df_sample.write_parquet(
            f'{self.test_dir}/TestData.parquet')

        # APIリクエスト
        request_data = {
            'filePath': f'{self.test_dir}/TestData.parquet',
            'tableName': 'TestLargeParquet'
        }
        response = self.client.post('/api/import-parquet-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestLargeParquet',
                         response_data['result']['tableName'])

        # データの検証
        df = self.tables_manager.get_table('TestLargeParquet').table
        self.assertEqual(True, df_sample.equals(df))

    def test_import_parquet_by_path_custom_table_name(self):
        """
        カスタムテーブル名でPARQUETファイルをインポートするテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_parquet(
            f'{self.test_dir}/Simple.parquet')

        # APIリクエスト
        request_data = {
            'filePath': f'{self.test_dir}/Simple.parquet',
            'tableName': 'MyCustomParquetTable'
        }
        response = self.client.post('/api/import-parquet-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('MyCustomParquetTable',
                         response_data['result']['tableName'])

        # データの検証
        df = self.tables_manager.get_table('MyCustomParquetTable').table
        self.assertEqual(True, test_data.equals(df))

    def test_import_parquet_by_path_file_not_exists(self):
        """
        存在しないファイルパスを指定した場合のテスト
        """
        request_data = {
            'filePath': '/non/existent/file.parquet',
            'tableName': 'TestNonExistent'
        }
        response = self.client.post('/api/import-parquet-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("filePath does not exist: /non/existent/file.parquet",
                      response_data['message'])

    def test_import_parquet_by_path_invalid_file_extension(self):
        """
        PARQUET以外のファイル拡張子を指定した場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_csv(
            f'{self.test_dir}/TestDataComma.csv')
        request_data = {
            'filePath': f'{self.test_dir}/TestDataComma.csv',
            'tableName': 'TestInvalidExtension'
        }
        response = self.client.post('/api/import-parquet-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Failed to parse PARQUET file: "
                      "Invalid format or encoding.",
                      response_data['message'])

    def test_import_parquet_by_path_missing_file_path(self):
        """
        filePathパラメータが未指定の場合のテスト
        """
        request_data = {
            'tableName': 'TestMissingPath'
        }
        response = self.client.post('/api/import-parquet-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("filePath is required", response_data['message'])

    def test_import_parquet_by_path_missing_table_name(self):
        """
        tableNameパラメータが未指定の場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_parquet(
            f'{self.test_dir}/Simple.parquet')
        request_data = {
            'filePath': f'{self.test_dir}/Simple.parquet'
        }
        response = self.client.post('/api/import-parquet-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("tableName is required.", response_data['message'])

    def test_import_parquet_by_path_duplicate_table_name(self):
        """
        既存のテーブル名と重複する場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_parquet(
            f'{self.test_dir}/Simple.parquet')
        # 先にテーブルを作成
        first_request_data = {
            'filePath': f'{self.test_dir}/Simple.parquet',
            'tableName': 'DuplicateTable'
        }
        self.client.post('/api/import-parquet-by-path',
                         data=json.dumps(first_request_data),
                         content_type='application/json')

        # 同じテーブル名で再度作成を試行
        second_request_data = {
            'filePath': f'{self.test_dir}/Simple.parquet',
            'tableName': 'DuplicateTable'
        }
        response = self.client.post('/api/import-parquet-by-path',
                                    data=json.dumps(second_request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        # テーブル名重複エラーメッセージを確認

    def test_import_parquet_by_path_invalid_json(self):
        """
        不正なJSONを送信した場合のテスト
        """
        response = self.client.post('/api/import-parquet-by-path',
                                    data='invalid json',
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Invalid JSON format", response_data['message'])

    def test_import_parquet_by_path_with_temporary_file(self):
        """
        一時的なPARQUETファイルを作成してインポートするテスト
        """
        # 一時的なPARQUETファイルを作成
        temp_data = pl.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['A', 'B', 'C', 'D', 'E'],
            'col3': [10.1, 20.2, 30.3, 40.4, 50.5]
        })

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet',
                                         delete=False) as f:
            temp_data.write_parquet(f.name)
            temp_path = f.name

        try:
            # APIリクエスト
            request_data = {
                'filePath': temp_path,
                'tableName': 'TestTempParquet'
            }
            response = self.client.post('/api/import-parquet-by-path',
                                        data=json.dumps(request_data),
                                        content_type='application/json')

            response_data = response.json()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual('OK', response_data['code'])
            self.assertEqual('TestTempParquet',
                             response_data['result']['tableName'])

            # データの検証
            df = self.tables_manager.get_table('TestTempParquet').table
            self.assertEqual(3, len(df.columns))  # 3列
            self.assertEqual(5, len(df))  # 5行
            self.assertEqual(True, temp_data.equals(df))
        finally:
            # 一時ファイルを削除
            os.unlink(temp_path)

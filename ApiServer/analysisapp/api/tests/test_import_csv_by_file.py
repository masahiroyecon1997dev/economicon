import shutil
import tempfile
import unittest

import polars as pl
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestApiImportCsvByFile(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テスト用の出力ディレクトリ
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_upload_valid_csv_file(self):
        """
        有効なCSVファイルをアップロードした場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_csv(
            f'{self.test_dir}/TestDataComma.csv', separator=',')
        test_file = File(open(f'{self.test_dir}/TestDataComma.csv', 'rb'))

        uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # レスポンスデータの検証
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestDataComma',
                         response_data['result']['tableName'])
        df = self.tables_manager.get_table('TestDataComma').table
        self.assertEqual(True, test_data.equals(df))

    def test_upload_csv_with_only_headers(self):
        """
        ヘッダーのみのCSVファイルをアップロードした場合のテスト
        問題なく読み込める
        """
        test_data = pl.DataFrame({
            'col_1': [],
            'col_2': [],
            'col_3': []
        })
        test_data.write_csv(
            f'{self.test_dir}/OnlyHeaderComma.csv', separator=',')
        test_file = File(open(f'{self.test_dir}/OnlyHeaderComma.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('OnlyHeaderComma.csv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('OnlyHeaderComma').table
        self.assertEqual(True, test_data.equals(df))

    def test_no_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト
        """
        response = self.client.post('/api/import-csv-by-file')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'], "No file uploaded.")

    def test_upload_non_csv_file(self):
        """
        CSVではないファイルをアップロードした場合のテスト (拡張子チェック)
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_json(
            f'{self.test_dir}/TestDataJson.json')
        test_file = File(open(f'{self.test_dir}/TestDataJson.json', 'rb'))
        uploaded_file = SimpleUploadedFile('TestDataJson.json',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Uploaded file is not a .csv file.",
                      response_data['message'])

    def test_upload_empty_csv_file(self):
        """
        空のCSVファイルをアップロードした場合のテスト (Polars NoDataError)
        """
        with open(f'{self.test_dir}/Empty.csv', 'w',
                  encoding='utf-8'):
            pass
        test_file = File(open(f'{self.test_dir}/Empty.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('Empty.csv', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(
            "Invalid file content type. Allowed types: text/csv, "
            "application/csv, text/plain",
            response_data['message'])

    @unittest.skip("このテストは現在、発生させる方法が不明なためスキップされています。")
    def test_upload_malformed_csv_file(self):
        """
        不正な形式のCSVファイルをアップロードした場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_parquet(
            f'{self.test_dir}/Error.csv')
        test_file = File(open(f'{self.test_dir}/Error.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('Error.csv', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Failed to parse CSV file: Invalid format or encoding.",
                      response_data['message'])

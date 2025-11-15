import shutil
import tempfile
import unittest

import polars as pl
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestApiImportTsvByFile(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テスト用の出力ディレクトリ
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_upload_valid_tsv_file(self):
        """
        有効なTSVファイルをアップロードした場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_csv(
            f'{self.test_dir}/TestDataTab1.tsv', separator='\t')
        test_file = File(open(f'{self.test_dir}/TestDataTab1.tsv',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab1.tsv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # レスポンスデータの検証
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestDataTab1', response_data['result']['tableName'])
        df = self.tables_manager.get_table('TestDataTab1').table
        self.assertEqual(True, test_data.equals(df))

    def test_upload_valid_tsv_file_with_txt_extension(self):
        """
        拡張子が.txtの有効なTSVファイルをアップロードした場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_csv(
            f'{self.test_dir}/TestDataTab2.txt', separator='\t')
        test_file = File(open(f'{self.test_dir}/TestDataTab2.txt',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab2.txt',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # レスポンスデータの検証
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestDataTab2', response_data['result']['tableName'])
        df = self.tables_manager.get_table('TestDataTab2').table
        self.assertEqual(True, test_data.equals(df))

    def test_upload_tsv_with_only_headers(self):
        """
        ヘッダーのみのTSVファイルをアップロードした場合のテスト
        問題なく読み込める
        """
        test_data = pl.DataFrame({
            'col_1': [],
            'col_2': [],
            'col_3': []
        })
        test_data.write_csv(
            f'{self.test_dir}/OnlyHeaderTab.txt', separator='\t')
        test_file = File(open(f'{self.test_dir}/OnlyHeaderTab.txt',
                              'rb'))
        uploaded_file = SimpleUploadedFile('OnlyHeaderTab.txt',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('OnlyHeaderTab').table
        self.assertEqual(True, test_data.equals(df))

    def test_no_tsv_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト
        """
        response = self.client.post('/api/import-tsv-by-file')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'], "No file uploaded.")

    def test_upload_non_tsv_file(self):
        """
        TSVではないファイルをアップロードした場合のテスト (拡張子チェック)
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_csv(
            f'{self.test_dir}/TestDataComma.csv', separator=',')
        test_file = File(open(f'{self.test_dir}/TestDataComma.csv',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Uploaded file is not a .tsv, .txt file.",
                      response_data['message'])

    def test_upload_empty_tsv_file(self):
        """
        空のTSVファイルをアップロードした場合のテスト (Polars NoDataError)
        """
        with open(f'{self.test_dir}/Empty.txt', 'w',
                  encoding='utf-8'):
            pass
        test_file = File(open(f'{self.test_dir}/Empty.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('Empty.txt', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(
            "Invalid file content type. Allowed types: "
            "text/tab-separated-values, text/plain",
            response_data['message'])

    @unittest.skip("このテストは現在、発生させる方法が不明なためスキップされています。")
    def test_upload_malformed_tsv_file(self):
        """
        不正な形式のTSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
        """
        test_file = File(open(f'{self.test_dir}/Error.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('Error.txt', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Invalid file content type. Allowed types: "
                      "text/tab-separated-values, text/plain",
                      response_data['message'])

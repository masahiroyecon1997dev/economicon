import shutil
import tempfile

import polars as pl
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestApiImportParquetByFile(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テスト用の出力ディレクトリ
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_upload_valid_parquet_file(self):
        """
        有効なParquetファイルをアップロードした場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_parquet(
            f'{self.test_dir}/TestData.parquet')
        test_file = File(open(f'{self.test_dir}/TestData.parquet',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestData.parquet',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-parquet-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # レスポンスデータの検証
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestData',
                         response_data['result']['tableName'])
        df = self.tables_manager.get_table('TestData').table
        self.assertEqual(True, test_data.equals(df))

    def test_no_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト。
        """
        response = self.client.post('/api/import-parquet-by-file')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'], "No file uploaded.")

    def test_upload_non_parquet_file(self):
        """
        Parquet以外のファイルをアップロードした場合のエラーケースをテストする。
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_csv(
            f'{self.test_dir}/TestDataComma.csv', separator=',')
        uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                           open(f'{self.test_dir}/'
                                                'TestDataComma.csv', 'rb'
                                                ).read(),
                                           content_type='multipart/form-data')

        response = self.client.post('/api/import-parquet-by-file',
                                    {'file': uploaded_file},
                                    format='multipart')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Uploaded file is not a .parquet file.",
                      response_data['message'])

    def test_upload_empty_parquet_file(self):
        """
        空のPARQUETファイルをアップロードした場合のテスト (Polars NoDataError)
        """
        # 一時的なPARQUETファイルを作成
        temp_data = pl.DataFrame()
        temp_data.write_parquet(
            f'{self.test_dir}/Empty.parquet')

        test_file = File(open(f'{self.test_dir}/Empty.parquet', 'rb'))
        uploaded_file = SimpleUploadedFile('Empty.parquet',
                                           test_file.read(),
                                           content_type='multipart/'
                                           'form-data')
        response = self.client.post('/api/import-parquet-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

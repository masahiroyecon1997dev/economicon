from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files import File
import tempfile
import os
from django.core.files.uploadedfile import SimpleUploadedFile
import polars as pl
from ..apis.data.tables_manager import TablesManager


class TestApiImportParquetByFile(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()

    def test_upload_valid_parquet_file(self):
        """
        有効なParquetファイルをアップロードした場合のテスト
        """
        compare_data = pl.read_parquet(
            '/AnalysisApp/AnalysisApp/SampleData/TestData.parquet')
        test_file = File(open('/AnalysisApp/AnalysisApp/SampleData/'
                              'TestData.parquet',
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
        self.assertEqual(True, compare_data.equals(df))

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
        test_file = File(open('/AnalysisApp/AnalysisApp/SampleData/'
                              'TestDataComma.csv',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                           test_file.read(),
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

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet',
                                         delete=False) as f:
            temp_data.write_parquet(f.name)
            temp_path = f.name

        try:
            test_file = File(open(temp_path, 'rb'))
            uploaded_file = SimpleUploadedFile('Empty.parquet',
                                               test_file.read(),
                                               content_type='multipart/'
                                               'form-data')
            response = self.client.post('/api/import-parquet-by-file',
                                        {'file': uploaded_file})

            response_data = response.json()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response_data['code'], 'OK')
        finally:
            # 一時ファイルを削除
            os.unlink(temp_path)

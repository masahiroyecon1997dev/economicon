from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
import polars as pl
from ..apis.data.tables_info import all_tables_info


class TestApiImportCsvByFile(APITestCase):

    def test_upload_valid_csv_file(self):
        """
        有効なCSVファイルをアップロードした場合のテスト
        """
        compare_data = pl.read_csv(
            '/AnalysisApp/SampleData/TestDataComma.csv',
            encoding='utf8')
        test_file = File(open('/AnalysisApp/SampleData/TestDataComma.csv',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # レスポンスデータの検証
        self.assertEqual('OK', response.json()['code'])
        self.assertEqual('TestDataComma',
                         response.json()['result']['tableName'])
        data = all_tables_info['TestDataComma'].table
        self.assertEqual(True, compare_data.equals(data))

    def test_upload_csv_with_only_headers(self):
        """
        ヘッダーのみのCSVファイルをアップロードした場合のテスト
        問題なく読み込める
        """
        compare_data = pl.read_csv(
            '/AnalysisApp/SampleData/OnlyHeaderComma.csv',
            encoding='utf8')
        test_file = File(open('/AnalysisApp/SampleData/OnlyHeaderComma.csv',
                              'rb'))
        uploaded_file = SimpleUploadedFile('OnlyHeaderComma.csv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['code'], 'OK')
        data = all_tables_info['OnlyHeaderComma'].table
        self.assertEqual(True, compare_data.equals(data))

    def test_no_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト
        """
        response = self.client.post('/api/import-csv-by-file')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['code'], 'NG')
        self.assertIn(response.json()['message'], "No file uploaded.")

    def test_upload_non_csv_file(self):
        """
        CSVではないファイルをアップロードした場合のテスト (拡張子チェック)
        """
        test_file = File(open('/AnalysisApp/SampleData/TestDataTab2.txt',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab2.txt',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['code'], 'NG')
        self.assertIn("Uploaded file is not a .csv file.",
                      response.json()['message'])

    def test_upload_empty_csv_file(self):
        """
        空のCSVファイルをアップロードした場合のテスト (Polars NoDataError)
        """
        test_file = File(open('/AnalysisApp/SampleData/Empty.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('Empty.csv', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['code'], 'NG')
        self.assertIn(
            "Invalid file content type. Allowed types: text/csv, "
            "application/csv, text/plain",
            response.json()['message'])

    def test_upload_malformed_csv_file(self):
        """
        不正な形式のCSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
        """
        test_file = File(open('/AnalysisApp/SampleData/Error.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('Error.csv', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['code'], 'NG')
        self.assertIn("Failed to parse CSV file: Invalid format or encoding.",
                      response.json()['message'])

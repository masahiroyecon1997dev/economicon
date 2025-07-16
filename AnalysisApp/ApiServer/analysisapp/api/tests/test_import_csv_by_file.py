from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
import polars as pl
from ..apis.data.tables_manager import TablesManager


class TestApiImportCsvByFile(APITestCase):

    def setUp(self):
        self.manager = TablesManager()
        self.manager.clear_tables()

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

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # レスポンスデータの検証
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestDataComma',
                         response_data['result']['tableName'])
        df = self.manager.get_table('TestDataComma').table
        self.assertEqual(True, compare_data.equals(df))

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

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.manager.get_table('OnlyHeaderComma').table
        self.assertEqual(True, compare_data.equals(df))

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
        test_file = File(open('/AnalysisApp/SampleData/TestDataTab2.txt',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab2.txt',
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
        test_file = File(open('/AnalysisApp/SampleData/Empty.csv', 'rb'))
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

    def test_upload_malformed_csv_file(self):
        """
        不正な形式のCSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
        """
        test_file = File(open('/AnalysisApp/SampleData/Error.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('Error.csv', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Failed to parse CSV file: Invalid format or encoding.",
                      response_data['message'])

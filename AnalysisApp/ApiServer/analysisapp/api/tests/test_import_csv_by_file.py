from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
import polars as pl
from ..apis.data.tables import tables


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
        self.assertEqual('OK', response.data['code'])
        self.assertEqual('TestDataComma', response.data['result']['tableName'])
        data = tables['TestDataComma']
        self.assertEqual(True, compare_data.equals(data))

    def test_upload_csv_with_only_headers(self):
        """
        ヘッダーのみのCSVファイルをアップロードした場合のテスト
        問題なく読み込める
        """
        compare_data = pl.read_csv(
            '/AnalysisApp/SampleData/OnlyHeader.csv',
            encoding='utf8')
        test_file = File(open('/AnalysisApp/SampleData/OnlyHeader.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('OnlyHeader.csv', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'OK')
        data = tables['OnlyHeader']
        self.assertEqual(True, compare_data.equals(data))

    def test_no_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト
        """
        response = self.client.post('/api/import-csv-by-file')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn(response.data['message'], 'No file uploaded.')

    def test_upload_non_csv_file(self):
        """
        CSVではないファイルをアップロードした場合のテスト (拡張子チェック)
        """
        test_file = File(open('/AnalysisApp/SampleData/TestDataTab.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab.txt', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn('Uploaded file is not a .csv file.',
                      response.data['message'])

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
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn(
            'The uploaded CSV file is empty or contains no valid data.',
            response.data['message'])

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
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn('An unexpected error occurred during CSV processing',
                      response.data['message'])

from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
import polars as pl
from ..apis.data.tables import tables


class TestApiImportTsvByFile(APITestCase):

    def test_upload_valid_tsv_file(self):
        """
        有効なTSVファイルをアップロードした場合のテスト
        """
        compare_data = pl.read_csv(
            '/AnalysisApp/SampleData/TestDataTab1.tsv',
            encoding='utf8', separator='\t')
        test_file = File(open('/AnalysisApp/SampleData/TestDataTab1.tsv',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab1.tsv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual('OK', response.data['code'])
        self.assertEqual('TestDataTab1', response.data['result']['tableName'])
        data = tables['TestDataTab1']
        self.assertEqual(True, compare_data.equals(data))

    def test_upload_valid_tsv_file_with_txt_extension(self):
        """
        拡張子が.txtの有効なTSVファイルをアップロードした場合のテスト
        """
        compare_data = pl.read_csv(
            '/AnalysisApp/SampleData/TestDataTab2.txt',
            encoding='utf8', separator='\t')
        test_file = File(open('/AnalysisApp/SampleData/TestDataTab2.txt',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab2.txt',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual('OK', response.data['code'])
        self.assertEqual('TestDataTab2', response.data['result']['tableName'])
        data = tables['TestDataTab2']
        self.assertEqual(True, compare_data.equals(data))

    def test_upload_tsv_with_only_headers(self):
        """
        ヘッダーのみのTSVファイルをアップロードした場合のテスト
        問題なく読み込める
        """
        compare_data = pl.read_csv(
            '/AnalysisApp/SampleData/OnlyHeaderTab.txt',
            separator='\t', has_header=True)
        test_file = File(open('/AnalysisApp/SampleData/OnlyHeaderTab.txt',
                              'rb'))
        uploaded_file = SimpleUploadedFile('OnlyHeaderTab.txt',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'OK')
        data = tables['OnlyHeaderTab']
        self.assertEqual(True, compare_data.equals(data))

    def test_no_tsv_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト
        """
        response = self.client.post('/api/import-tsv-by-file')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn(response.data['message'], "No file uploaded.")

    def test_upload_non_tsv_file(self):
        """
        TSVではないファイルをアップロードした場合のテスト (拡張子チェック)
        """
        test_file = File(open('/AnalysisApp/SampleData/TestDataComma.csv',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn("Uploaded file is not a .tsv, .txt file.",
                      response.data['message'])

    def test_upload_empty_tsv_file(self):
        """
        空のTSVファイルをアップロードした場合のテスト (Polars NoDataError)
        """
        test_file = File(open('/AnalysisApp/SampleData/Empty.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('Empty.txt', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn(
            "Invalid file content type. Allowed types: "
            "text/tab-separated-values, text/plain",
            response.data['message'])

    def test_upload_malformed_tsv_file(self):
        """
        不正な形式のTSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
        """
        test_file = File(open('/AnalysisApp/SampleData/Error.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('Error.txt', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn("Invalid file content type. Allowed types: "
                      "text/tab-separated-values, text/plain",
                      response.data['message'])

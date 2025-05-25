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
            '/AnalysisApp/SampleData/TestDataTab.tsv',
            encoding='utf8', eparator='\t')
        test_file = File(open('/AnalysisApp/SampleData/TestDataTab.tsv', 'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab.tsv',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual('OK', response.data['code'])
        self.assertEqual('TestDataTab', response.data['result']['tableName'])
        data = tables['TestDataTab']
        self.assertEqual(True, compare_data.equals(data))

    def test_upload_valid_tsv_file_with_txt_extension(self):
        """
        拡張子が.txtの有効なTSVファイルをアップロードした場合のテスト
        """
        compare_data = pl.read_csv(
            '/AnalysisApp/SampleData/TestDataTab.txt',
            encoding='utf8', eparator='\t')
        test_file = File(open('/AnalysisApp/SampleData/TestDataTab.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('TestDataTab.txt',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-tsv-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual('OK', response.data['code'])
        self.assertEqual('TestDataTab', response.data['result']['tableName'])
        self.assertEqual(len(tables), 2)
        data = tables['TestDataTab']
        self.assertEqual(True, compare_data.equals(data))

    def test_upload_tsv_with_only_headers(self):
        """
        ヘッダーのみのTSVファイルをアップロードした場合のテスト
        問題なく読み込める
        """
        compare_data = pl.read_csv(
            '/AnalysisApp/SampleData/OnlyHeader.csv',
            encoding='utf8', eparator='\t')
        test_file = File(open('/AnalysisApp/SampleData/OnlyHeader.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('OnlyHeader.csv', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-csv-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'OK')
        data = tables['OnlyHeader']
        self.assertEqual(True, compare_data.equals(data))

    def test_no_tsv_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト
        """
        response = self.client.post(self.upload_url, {}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn('No file uploaded.', response.data['message'])

    def test_upload_non_tsv_file(self):
        """
        TSVではないファイルをアップロードした場合のテスト (拡張子チェック)
        """
        csv_content = "a,b\n1,2\n"
        csv_file = SimpleUploadedFile(
            'test.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )

        response = self.client.post(self.upload_url, {'file': csv_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn('Uploaded file is not a TSV file.', response.data['message'])

    def test_upload_empty_tsv_file(self):
        """
        空のTSVファイルをアップロードした場合のテスト (Polars NoDataError)
        """
        tsv_content = "" # 空のファイル
        tsv_file = self._create_tsv_file(tsv_content)

        response = self.client.post(self.upload_url, {'file': tsv_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn('The uploaded TSV file is empty or contains no valid data.', response.data['message'])

    def test_upload_tsv_with_duplicate_headers(self):
        """
        重複ヘッダーを持つTSVファイルをアップロードした場合のテスト
        """
        tsv_content = """colA\tcolB\tcolA
1\t2\t3
4\t5\t6
"""
        tsv_file = self._create_tsv_file(tsv_content)

        response = self.client.post(self.upload_url, {'file': tsv_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn('The uploaded TSV file contains duplicate column names:', response.data['message'])
        self.assertIn('colA', response.data['message']) # メッセージに重複した列名が含まれるか確認

    def test_upload_malformed_tsv_file(self):
        """
        不正な形式のTSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
        """
        # タブ区切りが崩れている例
        malformed_tsv_content = """header1\theader2
1\t"broken_quote
2\t

from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
import polars as pl
from ..apis.data.tables_info import all_tables_info


class TestApiImportExcelByFile(APITestCase):

    def test_upload_valid_excel_file(self):
        """
        有効なExcel(xlsx)ファイルをアップロードした場合のテスト
        """
        compare_data = pl.read_excel(
            '/AnalysisApp/SampleData/TestDataXlsx.xlsx')
        test_file = File(open('/AnalysisApp/SampleData/TestDataXlsx.xlsx',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataXlsx.xlsx',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual('OK', response.data['code'])
        self.assertEqual('TestDataXlsx', response.data['result']['tableName'])
        data = all_tables_info['TestDataXlsx'].table
        self.assertEqual(True, compare_data.equals(data))

    def test_upload_valid_excel_file_with_extension_xls(self):
        """
        有効なExcel(xls)ファイルをアップロードした場合のテスト
        """
        compare_data = pl.read_excel(
            '/AnalysisApp/SampleData/TestDataXls.xls')
        test_file = File(open('/AnalysisApp/SampleData/TestDataXls.xls',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataXls.xls',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual('OK', response.data['code'])
        self.assertEqual('TestDataXls', response.data['result']['tableName'])
        data = all_tables_info['TestDataXls'].table
        self.assertEqual(True, compare_data.equals(data))

    def test_upload_excel_with_only_headers(self):
        """
        ヘッダーのみのEXCELファイルをアップロードした場合のテスト
        問題なく読み込める
        """
        compare_data = pl.read_excel(
            '/AnalysisApp/SampleData/OnlyHeaderExcel.xlsx')
        test_file = File(open('/AnalysisApp/SampleData/OnlyHeaderExcel.xlsx',
                              'rb'))
        uploaded_file = SimpleUploadedFile('OnlyHeaderExcel.xlsx',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'OK')
        data = all_tables_info['OnlyHeaderExcel'].table
        self.assertEqual(True, compare_data.equals(data))

    def test_no_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト。
        """
        response = self.client.post('/api/import-csv-by-file')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn(response.data['message'], "No file uploaded.")

    def test_upload_non_excel_file(self):
        """
        Excel以外のファイルをアップロードした場合のエラーケースをテストする。
        """
        test_file = File(open('/AnalysisApp/SampleData/TestDataComma.csv',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                           test_file.read(),
                                           content_type='multipart/form-data')

        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file},
                                    format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn("Uploaded file is not a .xlsx, .xls file.",
                      response.data['message'])

    def test_upload_empty_excel_file(self):
        """
        空のEXCELファイルをアップロードした場合のテスト (Polars NoDataError)
        """
        test_file = File(open('/AnalysisApp/SampleData/Empty.xlsx', 'rb'))
        uploaded_file = SimpleUploadedFile('Empty.xlsx', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn(
            "Invalid file content type. Allowed types: "
            "application/vnd.openxmlformats-officedocument.spreadsheetml."
            "sheet, application/vnd.ms-excel, application/CDFV2",
            response.data['message'])

    def test_upload_malformed_excel_file(self):
        """
        不正な形式のCSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
        """
        test_file = File(open('/AnalysisApp/SampleData/Error.xlsx', 'rb'))
        uploaded_file = SimpleUploadedFile('Error.xlsx', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'NG')
        self.assertIn("Invalid file content type. Allowed types: application/vnd.openxmlformats-"
                      "officedocument.spreadsheetml.sheet, application/vnd.ms-excel, application/CDFV2",
                      response.data['message'])

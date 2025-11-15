import shutil
import tempfile
import unittest

import polars as pl
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestApiImportExcelByFile(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テスト用の出力ディレクトリ
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_upload_valid_excel_file(self):
        """
        有効なExcel(xlsx)ファイルをアップロードした場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_excel(
            f'{self.test_dir}/TestDataXlsx.xlsx')
        test_file = File(open(f'{self.test_dir}/TestDataXlsx.xlsx',
                              'rb'))
        uploaded_file = SimpleUploadedFile(f'{self.test_dir}/TestDataXlsx.xlsx',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # レスポンスデータの検証
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestDataXlsx',
                         response_data['result']['tableName'])
        df = self.tables_manager.get_table('TestDataXlsx').table
        self.assertEqual(True, test_data.equals(df))

    @unittest.skip("このテストは現在、xlsが推奨されていないためスキップされています。")
    def test_upload_valid_excel_file_with_extension_xls(self):
        """
        有効なExcel(xls)ファイルをアップロードした場合のテスト
        """
        test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        test_data.write_excel(
            f'{self.test_dir}/TestDataXls.xls')
        compare_data = pl.read_excel(
            f'{self.test_dir}/TestDataXls.xls')
        test_file = File(open(f'{self.test_dir}/TestDataXls.xls',
                              'rb'))
        uploaded_file = SimpleUploadedFile('TestDataXls.xls',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        # レスポンスデータの検証
        self.assertEqual('OK', response_data['code'])
        self.assertEqual('TestDataXls', response_data['result']['tableName'])
        df = self.tables_manager.get_table('TestDataXls').table
        self.assertEqual(True, test_data.equals(df))

    def test_upload_excel_with_only_headers(self):
        """
        ヘッダーのみのEXCELファイルをアップロードした場合のテスト
        問題なく読み込める
        """
        test_data = pl.DataFrame({
            'col_1': [],
            'col_2': [],
            'col_3': []
        })
        test_data.write_excel(
            f'{self.test_dir}/OnlyHeaderExcel.xlsx')
        test_file = File(open(f'{self.test_dir}/OnlyHeaderExcel.xlsx',
                              'rb'))
        uploaded_file = SimpleUploadedFile(f'{self.test_dir}/'
                                           'OnlyHeaderExcel.xlsx',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('OnlyHeaderExcel').table
        self.assertEqual(True, test_data.equals(df))

    def test_no_file_uploaded(self):
        """
        ファイルがアップロードされていない場合のテスト。
        """
        response = self.client.post('/api/import-csv-by-file')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'], "No file uploaded.")

    def test_upload_non_excel_file(self):
        """
        Excel以外のファイルをアップロードした場合のエラーケースをテストする。
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
        uploaded_file = SimpleUploadedFile(f'{self.test_dir}/'
                                           'TestDataComma.csv',
                                           test_file.read(),
                                           content_type='multipart/form-data')

        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file},
                                    format='multipart')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Uploaded file is not a .xlsx, .xls file.",
                      response_data['message'])

    def test_upload_empty_excel_file(self):
        """
        空のEXCELファイルをアップロードした場合のテスト (Polars NoDataError)
        """
        test_data = pl.DataFrame()
        test_data.write_excel(
            f'{self.test_dir}/Empty.xlsx')
        test_file = File(open(f'{self.test_dir}/Empty.xlsx', 'rb'))
        uploaded_file = SimpleUploadedFile(f'{self.test_dir}/'
                                           'Empty.xlsx',
                                           test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(
            "The uploaded EXCEL file is empty or contains no valid data.",
            response_data['message'])

    @unittest.skip("このテストは現在、発生させる方法が不明なためスキップされています。")
    def test_upload_malformed_excel_file(self):
        """
        不正な形式のCSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
        """
        test_file = File(open('/AnalysisApp/AnalysisApp'
                              '/SampleData/Error.xlsx', 'rb'))
        uploaded_file = SimpleUploadedFile('Error.xlsx', test_file.read(),
                                           content_type='multipart/form-data')
        response = self.client.post('/api/import-excel-by-file',
                                    {'file': uploaded_file})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Invalid file content type. Allowed types: "
                      "application/vnd.openxmlformats-officedocument."
                      "spreadsheetml.sheet, application/vnd.ms-excel, "
                      "application/CDFV2",
                      response_data['message'])

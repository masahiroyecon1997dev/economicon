from rest_framework.test import APITestCase
from rest_framework import status
import json
import polars as pl
import tempfile
import os
import shutil
from ..apis.data.tables_manager import TablesManager


class TestApiExportExcelByPath(APITestCase):

    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()

        # テスト用のテーブルデータを作成
        self.test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        self.tables_manager.store_table('TestTable', self.test_data)

        # テスト用の出力ディレクトリ
        self.test_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_output_dir, ignore_errors=True)

    def test_export_excel_by_path_success(self):
        """
        EXCELファイルをエクスポートするテスト
        """

        # APIリクエスト
        request_data = {
            'tableName': 'TestTable',
            'directoryPath': self.test_output_dir,
            'fileName': 'test_output.xlsx'
        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        output_path = os.path.join(self.test_output_dir, 'test_output.xlsx')
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたEXCELファイルの内容を検証
        exported_data = pl.read_excel(output_path)
        self.assertEqual(True, self.test_data.equals(exported_data))

    def test_export_excel_by_path_with_xls_extension(self):
        """
        .xls拡張子でEXCELファイルをエクスポートするテスト
        注意: Polarsは常にXLSX形式で出力するため、拡張子に関わらずXLSX形式のファイルが作成される
        """

        # APIリクエスト
        request_data = {
            'tableName': 'TestTable',
            'directoryPath': self.test_output_dir,
            'fileName': 'test_output.xls'
        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        output_path = os.path.join(self.test_output_dir, 'test_output.xls')
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # Polarsは常にXLSX形式で出力するため、ファイルヘッダーをチェック
        with open(output_path, 'rb') as f:
            header = f.read(4)
            # XLSX形式のZIPヘッダー（PK）をチェック
            self.assertEqual(header[:2], b'PK')

        # 読み取りのためにファイルを一時的に.xlsx拡張子でコピー
        temp_xlsx_path = output_path + '.xlsx'
        shutil.copy2(output_path, temp_xlsx_path)
        
        try:
            # 出力されたEXCELファイルの内容を検証（XLSX形式として読み込み）
            exported_data = pl.read_excel(temp_xlsx_path)
            self.assertEqual(True, self.test_data.equals(exported_data))
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_xlsx_path):
                os.unlink(temp_xlsx_path)

    def test_export_excel_by_path_table_not_exists(self):
        """
        存在しないテーブル名を指定した場合のテスト
        """

        request_data = {
            'tableName': 'NonExistentTable',
            'directoryPath': self.test_output_dir,
            'fileName': 'test_output.xlsx',
        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("tableName 'NonExistentTable' does not exist",
                      response_data['message'])

    def test_export_excel_by_path_invalid_output_directory(self):
        """
        存在しない出力ディレクトリを指定した場合のテスト
        """

        request_data = {
            'tableName': 'TestTable',
            'directoryPath': '/non/existent/directory',
            'fileName': 'test_output.xlsx'
        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Directory does not exist: /non/existent/directory",
                      response_data['message'])

    def test_export_excel_by_path_missing_table_name(self):
        """
        tableNameパラメータが未指定の場合のテスト
        """

        request_data = {
            'directoryPath': self.test_output_dir,
            'fileName': 'test_output.xlsx'
        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("tableName is required", response_data['message'])

    def test_export_excel_by_path_missing_directory_path(self):
        """
        directoryPathパラメータが未指定の場合のテスト
        """
        request_data = {
            'tableName': 'TestTable',
            'fileName': 'test_output.xlsx'

        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("directoryPath is required", response_data['message'])

    def test_export_excel_by_path_missing_file_name(self):
        """
        fileNameパラメータが未指定の場合のテスト
        """
        request_data = {
            'tableName': 'TestTable',
            'directoryPath': self.test_output_dir,

        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("fileName is required", response_data['message'])

    def test_export_excel_by_path_invalid_json(self):
        """
        不正なJSONを送信した場合のテスト
        """
        response = self.client.post('/api/export-excel-by-path',
                                    data='invalid json',
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('NG', response_data['code'])
        self.assertIn("Invalid JSON format", response_data['message'])

    def test_export_excel_by_path_empty_table(self):
        """
        空のテーブルをエクスポートする場合のテスト
        """
        # 空のテーブルを作成
        empty_data = pl.DataFrame({'col1': [], 'col2': []})
        self.tables_manager.store_table('EmptyTable', empty_data)

        request_data = {
            'tableName': 'EmptyTable',
            'directoryPath': self.test_output_dir,
            'fileName': 'empty_output.xlsx'
        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        output_path = os.path.join(self.test_output_dir, 'empty_output.xlsx')
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたEXCELファイルの内容を検証（空のデータ）
        exported_data = pl.read_excel(output_path)
        self.assertEqual(True, empty_data.equals(exported_data))

    def test_export_excel_by_path_large_table(self):
        """
        大きなテーブルをエクスポートする場合のテスト
        """
        # 大きなテーブルを作成
        large_data = pl.DataFrame({
            'id': list(range(1000)),
            'value': [f'value_{i}' for i in range(1000)],
            'number': [i * 1.5 for i in range(1000)]
        })
        self.tables_manager.store_table('LargeTable', large_data)

        request_data = {
            'tableName': 'LargeTable',
            'directoryPath': self.test_output_dir,
            'fileName': 'large_output.xlsx'
        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        output_path = os.path.join(self.test_output_dir, 'large_output.xlsx')
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたEXCELファイルの内容を検証
        exported_data = pl.read_excel(output_path)
        self.assertEqual(True, large_data.equals(exported_data))
        self.assertEqual(1000, len(exported_data))  # 行数確認

    def test_export_excel_by_path_special_characters_in_data(self):
        """
        特殊文字を含むデータをエクスポートする場合のテスト
        """
        # 特殊文字を含むテーブルを作成
        special_data = pl.DataFrame({
            'text': ['日本語', 'English', '中文', '한국어'],
            'special': ['@#$%', '&*()[]', '{}|\\', '\'";:'],
            'numbers': [1.23, -4.56, 0.0, 999.999]
        })
        self.tables_manager.store_table('SpecialTable', special_data)

        request_data = {
            'tableName': 'SpecialTable',
            'directoryPath': self.test_output_dir,
            'fileName': 'special_output.xlsx'
        }
        response = self.client.post('/api/export-excel-by-path',
                                    data=json.dumps(request_data),
                                    content_type='application/json')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('OK', response_data['code'])
        output_path = os.path.join(self.test_output_dir, 'special_output.xlsx')
        self.assertEqual(output_path, response_data['result']['filePath'])

        # ファイルが作成されているかチェック
        self.assertTrue(os.path.exists(output_path))

        # 出力されたEXCELファイルの内容を検証
        exported_data = pl.read_excel(output_path)
        self.assertEqual(True, special_data.equals(exported_data))
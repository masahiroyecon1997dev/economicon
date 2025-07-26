from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json

from ..apis.data.tables_manager import TablesManager


class TestApiDuplicateColumn(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': ['x', 'y', 'z']
        })
        self.tables_manager.store_table('TestTable', df)

    def test_duplicate_column_success(self):
        # 正常に列複製できる
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_Copy'
        }
        response = self.client.post(
            '/api/duplicate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'TestTable')
        self.assertEqual(response_data['result']['columnName'], 'A_Copy')
        
        # 列が複製されているか確認
        df = self.tables_manager.get_table('TestTable').table
        expected_columns = ['A', 'A_Copy', 'B', 'C']
        self.assertEqual(df.columns, expected_columns)
        
        # 複製された列の値が元の列と同じか確認
        self.assertEqual(df['A'].to_list(), df['A_Copy'].to_list())
        self.assertEqual(df['A_Copy'].to_list(), [1, 2, 3])

    def test_duplicate_column_success_middle_column(self):
        # 中間の列を複製する場合
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'B',
            'newColumnName': 'B_Duplicate'
        }
        response = self.client.post(
            '/api/duplicate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # 列の順序が正しいか確認（B の右隣に B_Duplicate が挿入される）
        df = self.tables_manager.get_table('TestTable').table
        expected_columns = ['A', 'B', 'B_Duplicate', 'C']
        self.assertEqual(df.columns, expected_columns)
        
        # 複製された列の値が元の列と同じか確認
        self.assertEqual(df['B'].to_list(), df['B_Duplicate'].to_list())
        self.assertEqual(df['B_Duplicate'].to_list(), [4, 5, 6])

    def test_duplicate_column_success_string_column(self):
        # 文字列列の複製
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'C',
            'newColumnName': 'C_Clone'
        }
        response = self.client.post(
            '/api/duplicate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 複製された文字列列の値が正しいか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertEqual(df['C'].to_list(), df['C_Clone'].to_list())
        self.assertEqual(df['C_Clone'].to_list(), ['x', 'y', 'z'])

    def test_duplicate_column_invalid_table(self):
        # 存在しないテーブル名
        payload = {
            'tableName': 'NoTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_Copy'
        }
        response = self.client.post(
            '/api/duplicate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NoTable' does not exist.", response_data['message'])

    def test_duplicate_column_invalid_source_column(self):
        # 存在しないソース列名を指定
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'Z',
            'newColumnName': 'Z_Copy'
        }
        response = self.client.post(
            '/api/duplicate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "sourceColumnName 'Z' does not exist.")

    def test_duplicate_column_duplicate_new_column_name(self):
        # 既存の列名と同じ新列名を指定
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'B'  # 既存の列名
        }
        response = self.client.post(
            '/api/duplicate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("newColumnName 'B'", response_data['message'])
        self.assertIn("already exists", response_data['message'])
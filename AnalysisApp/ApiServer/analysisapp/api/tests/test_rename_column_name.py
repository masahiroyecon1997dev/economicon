from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_info import all_tables_info, TableInfo
import polars as pl


class TestApiRenameColumnName(APITestCase):
    def setUp(self):
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2],
            'B': [3, 4]
        })
        all_tables_info['TestTable'] = TableInfo(table_name='TestTable',
                                                 table=df)

    def tearDown(self):
        all_tables_info.clear()

    def test_rename_column_success(self):
        payload = {
            'tableName': 'TestTable',
            'oldColumnName': 'A',
            'newColumnName': 'C'
        }
        response = self.client.post(
            '/api/rename-column-name',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = all_tables_info['TestTable'].table
        self.assertIn('C', df.columns)
        self.assertNotIn('A', df.columns)
        self.assertEqual(df['C'].to_list(), [1, 2])

    def test_rename_column_not_found(self):
        payload = {
            'tableName': 'TestTable',
            'oldColumnName': 'Z',
            'newColumnName': 'C'
        }
        response = self.client.post(
            '/api/rename-column-name',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "columnName 'Z' does not exist.")

    def test_rename_column_empty_old_column_name(self):
        payload = {
            'tableName': 'TestTable',
            'oldColumnName': '',
            'newColumnName': 'C'
        }
        response = self.client.post(
            '/api/rename-column-name',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "columnName is required.")

    def test_rename_column_empty_new_column_name(self):
        payload = {
            'tableName': 'TestTable',
            'oldColumnName': 'A',
            'newColumnName': ''
        }
        response = self.client.post(
            '/api/rename-column-name',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "newColumnName is required.")

    def test_rename_column_table_not_found(self):
        # 存在しないテーブル名を指定した場合の異常系
        payload = {
            'tableName': 'NotExistTable',
            'oldColumnName': 'A',
            'newColumnName': 'C'
        }
        response = self.client.post(
            '/api/rename-column-name',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "tableName 'NotExistTable' does not exist.")

from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_manager import TablesManager
import polars as pl


class TestApiDeleteColumn(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': [7, 8, 9]
        })
        self.tables_manager.store_table('TestTable', df)

    def test_delete_column_success(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': 'A'
        }
        response = self.client.post(
            '/api/delete-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('TestTable').table
        self.assertNotIn('A', df.columns)
        self.assertIn('B', df.columns)
        self.assertIn('C', df.columns)

    def test_delete_column_not_found(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': 'Z'
        }
        response = self.client.post(
            '/api/delete-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "columnName 'Z' does not exist.")

    def test_delete_column_table_not_found(self):
        payload = {
            'tableName': 'NotExistTable',
            'columnName': 'A'
        }
        response = self.client.post(
            '/api/delete-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "tableName 'NotExistTable' does not exist.")

    def test_delete_column_empty_table_name(self):
        payload = {
            'tableName': '',
            'columnName': 'A'
        }
        response = self.client.post(
            '/api/delete-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "tableName is required.")

    def test_delete_column_empty_column_name(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': ''
        }
        response = self.client.post(
            '/api/delete-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "columnName is required.")

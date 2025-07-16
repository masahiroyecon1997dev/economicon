from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_manager import TablesManager
import polars as pl


class TestApiDeleteTable(APITestCase):
    def setUp(self):
        self.manager = TablesManager()
        self.manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2],
            'B': [3, 4]
        })
        self.manager.store_table('TestTable1', df)
        df = pl.DataFrame({
            'C': [1, 2],
            'D': [3, 4]
        })
        self.manager.store_table('TestTable1', df)

    def test_delete_table_success(self):
        payload = {
            'tableName': 'TestTable2'
        }
        response = self.client.post(
            '/api/delete-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertNotIn('TestTable2', self.manager.get_table_name_list())
        self.assertEqual(len(self.manager.get_table_name_list()), 1)

    def test_delete_table_not_found(self):
        payload = {
            'tableName': 'NotExistTable'
        }
        response = self.client.post(
            '/api/delete-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName 'NotExistTable' does not exist.")

    def test_delete_table_empty_table_name(self):
        payload = {
            'tableName': ''
        }
        response = self.client.post(
            '/api/delete-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName is required.")

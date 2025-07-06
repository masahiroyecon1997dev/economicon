from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_info import all_tables_info, TableInfo
import polars as pl


class TestApiRenameTableName(APITestCase):
    def setUp(self):
        all_tables_info.clear()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2],
            'B': [3, 4]
        })
        all_tables_info['OldTable'] = TableInfo(table_name='OldTable',
                                                table=df)

    def test_rename_table_success(self):
        payload = {
            'oldTableName': 'OldTable',
            'newTableName': 'NewTable'
        }
        response = self.client.post(
            '/api/rename-table-name',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(all_tables_info['NewTable'].table_name, 'NewTable')
        self.assertNotIn('OldTable', all_tables_info)
        df = all_tables_info['NewTable'].table
        self.assertTrue(df['A'].to_list() == [1, 2])
        self.assertTrue(df['B'].to_list() == [3, 4])

    def test_rename_table_not_found(self):
        payload = {
            'oldTableName': 'NotExist',
            'newTableName': 'AnyName'
        }
        response = self.client.post(
            '/api/rename-table-name',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName 'NotExist' does not exist.")

    def test_rename_table_empty_old_table_name(self):
        # oldTableNameが空
        payload = {
            'oldTableName': '',
            'newTableName': 'NewTable'
        }
        response = self.client.post(
            '/api/rename-table-name',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName is required.")

    def test_rename_table_empty_new_table_name(self):
        # newTableNameが空
        payload = {
            'oldTableName': 'OldTable',
            'newTableName': ''
        }
        response = self.client.post(
            '/api/rename-table-name',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName is required.")

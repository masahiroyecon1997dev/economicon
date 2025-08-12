from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_manager import TablesManager


class TestApiCreateTable(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()

    def test_create_table_success(self):
        payload = {
            'tableName': 'NewTable',
            'tableNumberOfRows': 3,
            'columnNames': ['A', 'B']
        }
        response = self.client.post(
            '/api/create-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        # テーブルが作成されているか
        self.assertIn('NewTable', self.tables_manager.get_table_name_list())
        df = self.tables_manager.get_table('NewTable').table
        self.assertEqual(df.shape, (3, 2))
        self.assertEqual(df.columns, ['A', 'B'])
        self.assertTrue(df['A'].to_list() == [None, None, None])

    def test_create_table_invalid_table_name(self):
        # テーブル名が空
        payload = {
            'tableName': '',
            'tableNumberOfRows': 2,
            'columnNames': ['A', 'B']
        }
        response = self.client.post(
            '/api/create-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName is required.")

    def test_create_table_invalid_number_of_rows(self):
        # テーブル行数が文字列
        payload = {
            'tableName': 'EmptyRowTable',
            'tableNumberOfRows': 'A',
            'columnNames': ['A', 'B']
        }
        response = self.client.post(
            '/api/create-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableNumberOfRows must be a number.")

    def test_create_table_invalid_columns(self):
        # columnsが空
        payload = {
            'tableName': 'EmptyColTable',
            'tableNumberOfRows': 2,
            'columnNames': []
        }
        response = self.client.post(
            '/api/create-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "columnNames must be with at least one item.")

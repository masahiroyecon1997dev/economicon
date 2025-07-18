from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_manager import TablesManager
import polars as pl


class TestApiInputCellData(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3, 4, 5, 6, 7, 1, 2, 3],
            'B': [4, 5, 6, 7, 8, 9, 10, 4, 5, 6]
        })
        self.tables_manager.store_table('TestTable', df)

    def test_input_cell_data_success(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': 'A',
            'rowIndex': 2,
            'newValue': 99
        }
        response = self.client.post(
            '/api/input-cell-data',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('TestTable').table
        self.assertEqual(df['A'][2], 99)

    def test_input_cell_data_success_with_string(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': 'A',
            'rowIndex': 1,
            'newValue': 'AAA'
        }
        response = self.client.post(
            '/api/input-cell-data',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('TestTable').table
        self.assertEqual(df['A'][1], 'AAA')

    def test_input_cell_data_invalid_table(self):
        payload = {
            'tableName': 'NoTable',
            'columnName': 'A',
            'rowIndex': 0,
            'newValue': 10
        }
        response = self.client.post(
            '/api/input-cell-data',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName 'NoTable' does not exist.")

    def test_input_cell_data_invalid_column(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': 'Z',
            'rowIndex': 0,
            'newValue': 10
        }
        response = self.client.post(
            '/api/input-cell-data',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "columnName 'Z' does not exist.")

    def test_input_cell_data_invalid_row_over(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': 'A',
            'rowIndex': 100,
            'newValue': 10
        }
        response = self.client.post(
            '/api/input-cell-data',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "rowIndex must be between 0 and 9.")

    def test_input_cell_data_invalid_row_string(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': 'A',
            'rowIndex': 'String',
            'newValue': 10
        }
        response = self.client.post(
            '/api/input-cell-data',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "rowIndex must be a number.")

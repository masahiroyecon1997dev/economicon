from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_manager import TablesManager
import polars as pl


class TestApiFilterSingleCondition(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3, 4, 5, 6, 7, 1, 2, 3],
            'B': [11, 12, 30, 40, 1, 2, 3, 40, 10, 2],
            'C': [1, 1, 4, 8, 4, 6, 7, 2, 3, 2]
        })
        self.tables_manager.store_table('TestTable', df)

    def test_filter_equals(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'A',
            'condition': 'equals',
            'isCompareColumn': 'false',
            'compareValue': 2
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        self.assertEqual(df.shape[0], 2)
        self.assertListEqual(df['A'].to_list(), [2, 2])

    def test_filter_greater_than(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'B',
            'condition': 'greaterThan',
            'isCompareColumn': 'false',
            'compareValue': 10
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        self.assertEqual(df.shape[0], 5)
        self.assertListEqual(df['B'].to_list(), [11, 12, 30, 40, 40])

    def test_filter_not_equals(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'A',
            'condition': 'notEquals',
            'isCompareColumn': 'false',
            'compareValue': 2
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        self.assertEqual(df.shape[0], 8)
        self.assertNotIn(2, df['A'].to_list())

    def test_filter_greater_than_or_equals(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'B',
            'condition': 'greaterThanOrEquals',
            'isCompareColumn': 'false',
            'compareValue': 30
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        self.assertEqual(df.shape[0], 3)
        self.assertListEqual(df['B'].to_list(), [30, 40, 40])

    def test_filter_less_than(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'A',
            'condition': 'lessThan',
            'isCompareColumn': 'false',
            'compareValue': 3
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        self.assertEqual(df.shape[0], 4)
        self.assertListEqual(df['A'].to_list(), [1, 2, 1, 2])

    def test_filter_less_than_or_equals(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'B',
            'condition': 'lessThanOrEquals',
            'isCompareColumn': 'false',
            'compareValue': 12
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        self.assertEqual(df.shape[0], 7)
        self.assertListEqual(df['B'].to_list(), [11, 12, 1, 2, 3, 10, 2])

    def test_filter_equals_compare_column(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'A',
            'condition': 'equals',
            'isCompareColumn': 'true',
            'compareValue': 'C'
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        # A==Cとなる行
        self.assertEqual(df.shape[0], 3)
        self.assertListEqual(df['A'].to_list(), [1, 6, 7])
        self.assertListEqual(df['C'].to_list(), [1, 6, 7])

    def test_filter_greater_than_compare_column(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'A',
            'condition': 'greaterThan',
            'isCompareColumn': 'true',
            'compareValue': 'C'
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        # B>Cとなる行
        self.assertEqual(df.shape[0], 3)
        self.assertListEqual(df['A'].to_list(), [2, 5, 3])
        self.assertListEqual(df['C'].to_list(), [1, 4, 2])

    def test_filter_less_than_or_equals_compare_column(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'A',
            'condition': 'lessThanOrEquals',
            'isCompareColumn': 'true',
            'compareValue': 'C'
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('FilteredTable').table
        # A<=C
        self.assertEqual(df.shape[0], 7)
        self.assertListEqual(df['A'].to_list(), [1, 3, 4, 6, 7, 1, 2])
        self.assertListEqual(df['C'].to_list(), [1, 4, 8, 6, 7, 2, 3])

    def test_filter_invalid_table(self):
        payload = {
            'tableName': 'NoTable',
            'newTableName': 'FilteredTable',
            'columnName': 'A',
            'condition': 'equals',
            'isCompareColumn': 'false',
            'compareValue': 1
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NoTable' does not exist.",
                      response_data['message'])

    def test_filter_invalid_column(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'Z',
            'condition': 'equals',
            'isCompareColumn': 'false',
            'compareValue': 1
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("columnName 'Z' does not exist.",
                      response_data['message'])

    def test_filter_invalid_condition(self):
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'FilteredTable',
            'columnName': 'A',
            'condition': 'invalid_condition',
            'isCompareColumn': 'false',
            'compareValue': 1
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("condition 'invalid_condition' is not supported.",
                      response_data['message'])

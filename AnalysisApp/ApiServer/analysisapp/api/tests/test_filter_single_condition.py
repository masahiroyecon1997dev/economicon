from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_info import all_tables_info, TableInfo
import polars as pl


class TestApiFilterSingleCondition(APITestCase):
    def setUp(self):
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3, 4],
            'B': [10, 20, 30, 40]
        })
        all_tables_info['TestTable'] = TableInfo(table_name='TestTable',
                                                 table=df)

    def tearDown(self):
        all_tables_info.clear()

    def test_filter_equals(self):
        payload = {
            'tableName': 'TestTable',
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
        df = all_tables_info['TestTable'].table
        self.assertEqual(df.shape[0], 1)
        self.assertEqual(df['A'][0], 2)

    def test_filter_greater_than(self):
        payload = {
            'tableName': 'TestTable',
            'columnName': 'B',
            'condition': 'greaterThan',
            'isCompareColumn': 'false',
            'compareValue': 15
        }
        response = self.client.post(
            '/api/filter-single-condition',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = all_tables_info['TestTable'].table
        self.assertEqual(df.shape[0], 3)
        self.assertListEqual(df['B'].to_list(), [20, 30, 40])

    def test_filter_invalid_table(self):
        payload = {
            'tableName': 'NoTable',
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

    def test_filter_invalid_column(self):
        payload = {
            'tableName': 'TestTable',
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

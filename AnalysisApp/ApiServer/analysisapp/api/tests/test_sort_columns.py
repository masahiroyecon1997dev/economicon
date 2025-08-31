from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json

from ..apis.data.tables_manager import TablesManager


class TestApiSortColumns(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [3, 1, 2],
            'B': [6, 4, 5],
            'C': ['c', 'a', 'b']
        })
        self.tables_manager.store_table('TestTable', df)

    def test_sort_single_column_ascending(self):
        # 単一列で昇順ソート
        payload = {
            'tableName': 'TestTable',
            'sortColumns': [
                {'columnName': 'A', 'ascending': True}
            ]
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'TestTable')

        # ソート結果を確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertEqual(df['A'].to_list(), [1, 2, 3])
        self.assertEqual(df['B'].to_list(), [4, 5, 6])
        self.assertEqual(df['C'].to_list(), ['a', 'b', 'c'])

    def test_sort_single_column_descending(self):
        # 単一列で降順ソート
        payload = {
            'tableName': 'TestTable',
            'sortColumns': [
                {'columnName': 'A', 'ascending': False}
            ]
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # ソート結果を確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertEqual(df['A'].to_list(), [3, 2, 1])
        self.assertEqual(df['B'].to_list(), [6, 5, 4])
        self.assertEqual(df['C'].to_list(), ['c', 'b', 'a'])

    def test_sort_multiple_columns(self):
        # 複数列でソート（混合順序）
        # より複雑なテストデータを準備
        df_complex = pl.DataFrame({
            'A': [1, 2, 1, 2],
            'B': [4, 3, 2, 1],
            'C': ['d', 'c', 'b', 'a']
        })
        self.tables_manager.update_table('TestTable', df_complex)

        payload = {
            'tableName': 'TestTable',
            'sortColumns': [
                {'columnName': 'A', 'ascending': True},
                {'columnName': 'B', 'ascending': False}
            ]
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # ソート結果を確認（A昇順、B降順）
        df = self.tables_manager.get_table('TestTable').table
        self.assertEqual(df['A'].to_list(), [1, 1, 2, 2])
        self.assertEqual(df['B'].to_list(), [4, 2, 3, 1])
        self.assertEqual(df['C'].to_list(), ['d', 'b', 'c', 'a'])

    def test_sort_invalid_table(self):
        # 存在しないテーブル名
        payload = {
            'tableName': 'NoTable',
            'sortColumns': [
                {'columnName': 'A', 'ascending': True}
            ]
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName 'NoTable' does not exist.")

    def test_sort_invalid_column(self):
        # 存在しないカラム名を指定
        payload = {
            'tableName': 'TestTable',
            'sortColumns': [
                {'columnName': 'Z', 'ascending': True}
            ]
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "columnName 'Z' does not exist.")

    def test_sort_empty_columns(self):
        # 空のソート列指定
        payload = {
            'tableName': 'TestTable',
            'sortColumns': []
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')

    def test_sort_missing_column_name(self):
        # columnNameが欠けている
        payload = {
            'tableName': 'TestTable',
            'sortColumns': [
                {'ascending': True}
            ]
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')

    def test_sort_missing_ascending(self):
        # ascendingが欠けている
        payload = {
            'tableName': 'TestTable',
            'sortColumns': [
                {'columnName': 'A'}
            ]
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')

    def test_sort_invalid_ascending_type(self):
        # ascendingがboolean以外
        payload = {
            'tableName': 'TestTable',
            'sortColumns': [
                {'columnName': 'A', 'ascending': 'true'}
            ]
        }
        response = self.client.post(
            '/api/sort-columns',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')

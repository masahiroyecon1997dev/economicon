from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json

from ..apis.data.tables_manager import TablesManager


class TestApiAddColumn(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        self.tables_manager.store_table('TestTable', df)

    def test_add_column_success(self):
        # 正常にカラム追加できる
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'C',
            'addPositionColumn': 'A'
        }
        response = self.client.post(
            '/api/add-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        # カラムが追加されているか
        df = self.tables_manager.get_table('TestTable').table
        index_C = df.columns.index('A') + 1
        self.assertEqual(df.columns[index_C], 'C')
        # 追加カラムはNoneで埋まっている
        self.assertTrue(df['C'].to_list() == [None, None, None])

    def test_add_column_invalid_table(self):
        # 存在しないテーブル名
        payload = {
            'tableName': 'NoTable',
            'newColumnName': 'C',
            'addPositionColumn': 'A'
        }
        response = self.client.post(
            '/api/add-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "tableName 'NoTable' does not exist.")

    def test_add_column_invalid_column(self):
        # 存在しないカラム名を指定
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'C',
            'addPositionColumn': 'Z'
        }
        response = self.client.post(
            '/api/add-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "addPositionColumn 'Z' does not exist.")

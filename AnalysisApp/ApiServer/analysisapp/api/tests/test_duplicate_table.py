from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json

from ..apis.data.tables_manager import TablesManager


class TestApiDuplicateTable(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': ['x', 'y', 'z']
        })
        self.tables_manager.store_table('TestTable', df)

    def test_duplicate_table_success(self):
        # 正常にテーブル複製できる
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'DuplicatedTable'
        }
        response = self.client.post(
            '/api/duplicate-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'],
                         'DuplicatedTable')

        # 複製されたテーブルが存在することを確認
        table_list = self.tables_manager.get_table_name_list()
        self.assertIn('DuplicatedTable', table_list)

        # 複製されたテーブルの内容が元のテーブルと同じことを確認
        original_df = self.tables_manager.get_table('TestTable').table
        duplicated_df = self.tables_manager.get_table('DuplicatedTable').table

        # データフレームの内容が同じかチェック
        self.assertTrue(original_df.equals(duplicated_df))

        # 列名が同じかチェック
        self.assertEqual(original_df.columns, duplicated_df.columns)

        # データが同じかチェック
        self.assertEqual(original_df['A'].to_list(),
                         duplicated_df['A'].to_list())
        self.assertEqual(original_df['B'].to_list(),
                         duplicated_df['B'].to_list())
        self.assertEqual(original_df['C'].to_list(),
                         duplicated_df['C'].to_list())

    def test_duplicate_table_invalid_source_table(self):
        # 存在しないソーステーブル名
        payload = {
            'tableName': 'NonExistentTable',
            'newTableName': 'DuplicatedTable'
        }
        response = self.client.post(
            '/api/duplicate-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NonExistentTable' does not exist",
                      response_data['message'])

    def test_duplicate_table_existing_destination_table(self):
        # 既に存在するテーブル名を新しいテーブル名として指定
        payload = {
            'tableName': 'TestTable',
            'newTableName': 'TestTable'  # 既に存在するテーブル名
        }
        response = self.client.post(
            '/api/duplicate-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("newTableName 'TestTable' already exists",
                      response_data['message'])

    def test_duplicate_table_empty_table(self):
        # 空のテーブルを複製
        empty_df = pl.DataFrame({
            'Col1': [],
            'Col2': []
        })
        self.tables_manager.store_table('EmptyTable', empty_df)

        payload = {
            'tableName': 'EmptyTable',
            'newTableName': 'DuplicatedEmptyTable'
        }
        response = self.client.post(
            '/api/duplicate-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'],
                         'DuplicatedEmptyTable')

        # 空のテーブルも正しく複製されることを確認
        duplicated_df = self.tables_manager.get_table(
            'DuplicatedEmptyTable').table
        self.assertEqual(duplicated_df.height, 0)  # 行数が0
        self.assertEqual(duplicated_df.columns, ['Col1', 'Col2'])  # 列名は保持

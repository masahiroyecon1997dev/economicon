from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_manager import TablesManager
import polars as pl


class TestApiCreateUnionTable(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()

        # 第1テーブル
        table1_df = pl.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['Tokyo', 'Osaka', 'Kyoto']
        })
        self.tables_manager.store_table('Table1', table1_df)

        # 第2テーブル
        table2_df = pl.DataFrame({
            'id': [4, 5, 6],
            'name': ['David', 'Eve', 'Frank'],
            'age': [28, 32, 40],
            'city': ['Nagoya', 'Kobe', 'Sendai']
        })
        self.tables_manager.store_table('Table2', table2_df)

        # 第3テーブル
        table3_df = pl.DataFrame({
            'id': [7, 8],
            'name': ['Grace', 'Henry'],
            'age': [27, 33],
            'city': ['Hiroshima', 'Fukuoka']
        })
        self.tables_manager.store_table('Table3', table3_df)

        # 列構成が異なるテーブル
        different_table_df = pl.DataFrame({
            'id': [9, 10],
            'username': ['user1', 'user2'],
            'score': [100, 200]
        })
        self.tables_manager.store_table('DifferentTable', different_table_df)

    def test_union_two_tables_all_columns(self):
        payload = {
            'unionTableName': 'UnionTable',
            'tableNames': ['Table1', 'Table2'],
            'columnNames': ['id', 'name', 'age', 'city']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        df = self.tables_manager.get_table('UnionTable').table
        self.assertEqual(df.shape, (6, 4))
        self.assertListEqual(df['id'].to_list(), [1, 2, 3, 4, 5, 6])
        self.assertListEqual(df['name'].to_list(),
                             ['Alice', 'Bob', 'Charlie',
                              'David', 'Eve', 'Frank'])

    def test_union_three_tables_selected_columns(self):
        payload = {
            'unionTableName': 'UnionTable',
            'tableNames': ['Table1', 'Table2', 'Table3'],
            'columnNames': ['id', 'name']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        df = self.tables_manager.get_table('UnionTable').table
        self.assertEqual(df.shape, (8, 2))
        self.assertListEqual(df['id'].to_list(), [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertListEqual(df['name'].to_list(),
                             ['Alice', 'Bob', 'Charlie',
                              'David', 'Eve', 'Frank', 'Grace', 'Henry'])

    def test_union_table_name_empty(self):
        payload = {
            'unionTableName': '',
            'tableNames': ['Table1', 'Table2'],
            'columnNames': ['id', 'name']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("unionTableName is required.",
                      response_data['message'])

    def test_union_table_name_already_exists(self):
        payload = {
            'unionTableName': 'Table1',  # 既存のテーブル名
            'tableNames': ['Table2', 'Table3'],
            'columnNames': ['id', 'name']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("unionTableName 'Table1' already exists.",
                      response_data['message'])

    def test_single_table_in_list(self):
        payload = {
            'unionTableName': 'UnionTable',
            'tableNames': ['Table1'],  # 1つのテーブルのみ
            'columnNames': ['id', 'name']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableNames must be with at least 2 tableName.",
                      response_data['message'])

    def test_nonexistent_table(self):
        payload = {
            'unionTableName': 'UnionTable',
            'tableNames': ['Table1', 'NonExistentTable'],
            'columnNames': ['id', 'name']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableNames 'NonExistentTable' does not exist.",
                      response_data['message'])

    def test_empty_column_names(self):
        payload = {
            'unionTableName': 'UnionTable',
            'tableNames': ['Table1', 'Table2'],
            'columnNames': []  # 空の列名リスト
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("columnNames must be with "
                      "at least 1 columnName.",
                      response_data['message'])

    def test_nonexistent_column_in_first_table(self):
        payload = {
            'unionTableName': 'UnionTable',
            'tableNames': ['Table1', 'Table2'],
            'columnNames': ['id', 'nonexistent_column']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("columnNames 'nonexistent_column' does not exist.",
                      response_data['message'])

    def test_column_missing_in_one_table(self):
        payload = {
            'unionTableName': 'UnionTable',
            # DifferentTableには'name'列がない
            'tableNames': ['Table1', 'DifferentTable'],
            'columnNames': ['id', 'name']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("columnNames 'name' does not exist.",
                      response_data['message'])

    def test_union_preserves_column_order(self):
        payload = {
            'unionTableName': 'UnionTable',
            'tableNames': ['Table1', 'Table2'],
            'columnNames': ['name', 'id', 'age']  # 元の順序と異なる
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        df = self.tables_manager.get_table('UnionTable').table
        # 指定された順序で列が並んでいることを確認
        self.assertListEqual(df.columns, ['name', 'id', 'age'])

    def test_missing_request_fields(self):
        # unionTableNameが欠けている場合
        payload = {
            'tableNames': ['Table1', 'Table2'],
            'columnNames': ['id', 'name']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

        # tableNamesが欠けている場合
        payload = {
            'unionTableName': 'UnionTable',
            'columnNames': ['id', 'name']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

        # columnNamesが欠けている場合
        payload = {
            'unionTableName': 'UnionTable',
            'tableNames': ['Table1', 'Table2']
        }
        response = self.client.post(
            '/api/create-union-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

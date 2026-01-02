from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl

from ..apis.data.tables_manager import TablesManager


class TestApiClearTables(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルを複数セット
        df1 = pl.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        df2 = pl.DataFrame({
            'X': [10, 20],
            'Y': [30, 40]
        })
        self.tables_manager.store_table('TestTable1', df1)
        self.tables_manager.store_table('TestTable2', df2)

    def test_clear_tables_success(self):
        # テーブルが存在することを確認
        table_names = self.tables_manager.get_table_name_list()
        self.assertEqual(len(table_names), 2)
        self.assertIn('TestTable1', table_names)
        self.assertIn('TestTable2', table_names)

        # テーブルをクリア
        response = self.client.delete('/api/clear-tables')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # テーブルが空になっていることを確認
        table_names = self.tables_manager.get_table_name_list()
        self.assertEqual(len(table_names), 0)

    def test_clear_tables_empty(self):
        # 既にテーブルをクリア
        self.tables_manager.clear_tables()
        
        # テーブルが空であることを確認
        table_names = self.tables_manager.get_table_name_list()
        self.assertEqual(len(table_names), 0)

        # 空の状態でクリアを実行
        response = self.client.delete('/api/clear-tables')

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # テーブルが空のままであることを確認
        table_names = self.tables_manager.get_table_name_list()
        self.assertEqual(len(table_names), 0)

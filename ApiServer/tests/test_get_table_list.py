from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestApiGetTableListAPI(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()

    def test_get_table_name_list_empty(self):
        # テーブルが0件の場合
        response = self.client.get('/api/get-table-list',
                                   content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableNameList'], [])

    def test_get_table_name_list_multiple(self):
        # テーブルが複数件の場合
        table_names = ['table1', 'table2', 'table3']
        import polars as pl
        for name in table_names:
            df = pl.DataFrame({'col': [1, 2, 3]})
            self.tables_manager.store_table(name, df)
        response = self.client.get('/api/get-table-list')
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertCountEqual(response_data['result']['tableNameList'],
                              table_names)

    def test_get_table_name_list_exception(self):
        # 例外発生時のテスト
        # TablesManager.get_table_name_list を一時的に例外を投げるようにモンキーパッチ
        original_method = self.tables_manager.get_table_name_list

        def raise_exception():
            raise Exception("DB error")
        self.tables_manager.get_table_name_list = raise_exception

        response = self.client.get('/api/get-table-list')
        response_data = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn('An unexpected error during '
                      'getting table name list.',
                      response_data['message'])

        # 後始末
        self.tables_manager.get_table_name_list = original_method

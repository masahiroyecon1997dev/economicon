import polars as pl
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils.translation import gettext as _

from ..apis.data.tables_manager import TablesManager


class TestApiGetColumnInfoListAPI(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        self.table_name = "test_table"
        # 作成するテーブルは2カラムとする
        self.test_data = pl.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })
        self.tables_manager.store_table(self.table_name, self.test_data)

    def test_get_column_info_list_success(self):
        # 正常系テスト：テーブルが存在する場合
        response = self.client.get(f'/api/get-column-info-list'
                                   f'?tableName={self.table_name}',
                                   content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        result = response_data['result']
        self.assertEqual(result['tableName'], self.table_name)
        # カラム名はDataFrameのスキーマ順に返ると想定
        expected_columns = [{'name': name, 'type': dtype}
                            for name, dtype
                            in test_data.items()]
        self.assertEqual(result['columnNameList'], expected_columns)

    def test_get_column_info_list_table_not_found(self):
        # 異常系テスト：存在しないテーブル名の場合
        response = self.client.get('/api/get-column-info-list',
                                   content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # エラーメッセージにテーブル名が存在しない旨が含まれることを確認
        self.assertIn("does not exist", response_data['message'])

    def test_get_column_info_list_exception(self):
        # 例外発生時のテスト
        # TablesManager.get_column_info_list を一時的に例外を投げるようにモンキーパッチ
        original_method = self.tables_manager.get_column_info_list

        # def raise_exception(table_name: str) -> List[str]:
        #     raise Exception("DB error")
        # self.tables_manager.get_column_name_list = raise_exception

        response = self.client.get(f'/api/get-column-info-list'
                                   f'?tableName={self.table_name}',
                                   content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(_("An unexpected error occurred during "
                        "getting column name list processing"),
                      response_data['message'])
        # 後始末
        self.tables_manager.get_column_name_list = original_method

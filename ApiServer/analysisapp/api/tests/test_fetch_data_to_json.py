import polars as pl
from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestApiFetchDataToJsonAPI(APITestCase):
    def setUp(self):
        # テスト用のテーブルをセットアップ
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        self.table_name = "test_table"
        self.test_data = pl.DataFrame({
            "column1": [1, 2, 3, 4, 5],
            "column2": ["a", "b", "c", "d", "e"]
        })
        self.tables_manager.store_table(self.table_name, self.test_data)

    def test_fetch_data_to_json_success(self):
        # 正常系テスト: JSONデータを取得
        start_row = 2
        fetch_rows = 2
        response = self.client.get(
            f'/api/fetch-data-to-json?tableName={self.table_name}'
            f'&startRow={start_row}&fetchRows={fetch_rows}',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data["result"]["tableName"], self.table_name)
        # メタ情報の確認
        self.assertEqual(response_data["result"]["totalRows"], 5)
        self.assertEqual(response_data["result"]["startRow"], start_row)
        self.assertEqual(response_data["result"]["endRow"],
                         start_row + fetch_rows - 1)
        # データの内容を確認
        data = response_data["result"]["data"]
        expected_data = self.test_data[1:3].write_json()
        self.assertEqual(data, expected_data)

    def test_fetch_data_to_json_table_not_found(self):
        # 異常系テスト: 存在しないテーブル名
        not_existent_table = "non_existent_table"
        start_row = 1
        fetch_rows = 3
        response = self.client.get(
            f'/api/fetch-data-to-json?tableName={not_existent_table}'
            f'&startRow={start_row}&fetchRows={fetch_rows}',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "tableName 'non_existent_table' does not exist.")

    def test_fetch_data_to_json_invalid_start_row_range(self):
        # 異常系テスト: 無効な行範囲 startRow
        start_row = 0
        fetch_rows = 4
        response = self.client.get(
            f'/api/fetch-data-to-json?tableName={self.table_name}'
            f'&startRow={start_row}&fetchRows={fetch_rows}',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "startRow must be between 1 and 5.")

    def test_fetch_data_to_json_invalid_fetch_rows(self):
        # 異常系テスト: 無効な取得行数 fetchRows
        start_row = 1
        fetch_rows = 0
        response = self.client.get(
            f'/api/fetch-data-to-json?tableName={self.table_name}'
            f'&startRow={start_row}&fetchRows={fetch_rows}',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "fetchRows must be a positive integer.")

    def test_fetch_data_to_json_missing_table_name(self):
        # 異常系テスト: 必須パラメータが不足している場合（tableName）
        not_table_name = ""
        start_row = 1
        fetch_rows = 6
        response = self.client.get(
            f'/api/fetch-data-to-json?tableName={not_table_name}'
            f'&startRow={start_row}&fetchRows={fetch_rows}',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "tableName is required.")

    def test_fetch_data_to_json_missing_start_row(self):
        # 異常系テスト: 必須パラメータが不足している場合（startRow）
        start_row = ""
        fetch_rows = 6
        response = self.client.get(
            f'/api/fetch-data-to-json?tableName={self.table_name}'
            f'&startRow={start_row}&fetchRows={fetch_rows}',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "startRow is required.")

    def test_fetch_data_to_json_missing_fetch_rows(self):
        # 異常系テスト: 必須パラメータが不足している場合（fetchRows）
        start_row = 1
        fetch_rows = ""
        response = self.client.get(
            f'/api/fetch-data-to-json?tableName={self.table_name}'
            f'&startRow={start_row}&fetchRows={fetch_rows}',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "fetchRows is required.")

    def test_fetch_data_to_json_fetch_beyond_table(self):
        # 正常系テスト: テーブルの行数を超える取得行数
        start_row = 3
        fetch_rows = 10  # テーブルは5行なので3行目から最後までの3行を取得
        response = self.client.get(
            f'/api/fetch-data-to-json?tableName={self.table_name}'
            f'&startRow={start_row}&fetchRows={fetch_rows}',
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        # メタ情報の確認
        self.assertEqual(response_data["result"]["totalRows"], 5)
        self.assertEqual(response_data["result"]["startRow"], start_row)
        self.assertEqual(response_data["result"]["endRow"], 5)  # 最後の行
        # データの内容を確認（3行目から最後まで）
        data = response_data["result"]["data"]
        expected_data = self.test_data[2:5].write_json()
        self.assertEqual(data, expected_data)

from rest_framework.test import APITestCase
from rest_framework import status
from ..apis.data.tables_manager import TablesManager
import polars as pl
import json


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
        payload = {
            "tableName": self.table_name,
            "firstRow": 2,
            "lastRow": 4
        }
        response = self.client.post(
            '/api/fetch-data-to-json',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data["result"]["tableName"], self.table_name)
        # データの内容を確認
        data = response_data["result"]["data"]
        expected_data = self.test_data[1:3].write_json()
        self.assertEqual(data, expected_data)

    def test_fetch_data_to_json_table_not_found(self):
        # 異常系テスト: 存在しないテーブル名
        payload = {
            "tableName": "non_existent_table",
            "firstRow": 1,
            "lastRow": 3
        }
        response = self.client.post(
            '/api/fetch-data-to-json',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "tableName 'non_existent_table' does not exist.")

    def test_fetch_data_to_json_invalid_first_row_range(self):
        # 異常系テスト: 無効な行範囲 firstRow
        payload = {
            "tableName": self.table_name,
            "firstRow": 0,
            "lastRow": 4
        }
        response = self.client.post(
            '/api/fetch-data-to-json',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "firstRow must be between 1 and 5.")

    def test_fetch_data_to_json_invalid_last_row_range(self):
        # 異常系テスト: 無効な行範囲 firstRow
        payload = {
            "tableName": self.table_name,
            "firstRow": 1,
            "lastRow": 6
        }
        response = self.client.post(
            '/api/fetch-data-to-json',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "lastRow must be between 1 and 5.")

    def test_fetch_data_to_json_missing_table_name(self):
        # 異常系テスト: 必須パラメータが不足している場合（tableName）
        payload = {
            "tableName": "",
            "firstRow": 1,
            "lastRow": 6
        }
        response = self.client.post(
            '/api/fetch-data-to-json',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "tableName is required.")

    def test_fetch_data_to_json_missing_first_row(self):
        # 異常系テスト: 必須パラメータが不足している場合（firstRow）
        payload = {
            "tableName": self.table_name,
            "firstRow": "",
            "lastRow": 6
        }
        response = self.client.post(
            '/api/fetch-data-to-json',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "firstRow is required.")

    def test_fetch_data_to_json_missing_last_row(self):
        # 異常系テスト: 必須パラメータが不足している場合（lastRow）
        payload = {
            "tableName": self.table_name,
            "firstRow": 1,
            "lastRow": ""
        }
        response = self.client.post(
            '/api/fetch-data-to-json',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response_data['message'],
                      "lastRow is required.")

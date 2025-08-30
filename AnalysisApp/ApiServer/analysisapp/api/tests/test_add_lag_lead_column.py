from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json

from ..apis.data.tables_manager import TablesManager


class TestApiAddLagLeadColumn(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'group': ['A', 'A', 'A', 'B', 'B', 'B'],
            'time': [1, 2, 3, 1, 2, 3],
            'value': [10, 20, 30, 40, 50, 60]
        })
        self.tables_manager.store_table('TestTable', df)

    def test_add_lag_column_success_no_group(self):
        # グループなしでラグ変数を追加
        payload = {
            'tableName': 'TestTable',
            'sourceColumn': 'value',
            'newColumnName': 'value_lag1',
            'periods': -1,
            'groupColumns': []
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # ラグ変数が正しく追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('value_lag1', df.columns)
        lag_values = df['value_lag1'].to_list()
        # 最初の値はNone、以降は前の値
        expected = [None, 10, 20, 30, 40, 50]
        self.assertEqual(lag_values, expected)

    def test_add_lead_column_success_no_group(self):
        # グループなしでリード変数を追加
        payload = {
            'tableName': 'TestTable',
            'sourceColumn': 'value',
            'newColumnName': 'value_lead1',
            'periods': 1,
            'groupColumns': []
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # リード変数が正しく追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('value_lead1', df.columns)
        lead_values = df['value_lead1'].to_list()
        # 次の値、最後はNone
        expected = [20, 30, 40, 50, 60, None]
        self.assertEqual(lead_values, expected)

    def test_add_lag_column_success_with_group(self):
        # グループありでラグ変数を追加
        payload = {
            'tableName': 'TestTable',
            'sourceColumn': 'value',
            'newColumnName': 'value_lag1_grouped',
            'periods': -1,
            'groupColumns': ['group']
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # グループ内でのラグ変数が正しく追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('value_lag1_grouped', df.columns)
        lag_values = df['value_lag1_grouped'].to_list()
        # 各グループの最初の値はNone
        expected = [None, 10, 20, None, 40, 50]
        self.assertEqual(lag_values, expected)

    def test_add_lead_column_success_with_group(self):
        # グループありでリード変数を追加
        payload = {
            'tableName': 'TestTable',
            'sourceColumn': 'value',
            'newColumnName': 'value_lead1_grouped',
            'periods': 1,
            'groupColumns': ['group']
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # グループ内でのリード変数が正しく追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('value_lead1_grouped', df.columns)
        lead_values = df['value_lead1_grouped'].to_list()
        # 各グループの最後の値はNone
        expected = [20, 30, None, 50, 60, None]
        self.assertEqual(lead_values, expected)

    def test_add_lag_lead_column_invalid_table(self):
        # 存在しないテーブル名
        payload = {
            'tableName': 'NoTable',
            'sourceColumn': 'value',
            'newColumnName': 'value_lag1',
            'periods': -1,
            'groupColumns': []
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NoTable' does not exist.",
                      response_data['message'])

    def test_add_lag_lead_column_invalid_source_column(self):
        # 存在しないソース列名
        payload = {
            'tableName': 'TestTable',
            'sourceColumn': 'nonexistent',
            'newColumnName': 'value_lag1',
            'periods': -1,
            'groupColumns': []
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("sourceColumn 'nonexistent' does not exist.",
                      response_data['message'])

    def test_add_lag_lead_column_invalid_group_column(self):
        # 存在しないグループ列名
        payload = {
            'tableName': 'TestTable',
            'sourceColumn': 'value',
            'newColumnName': 'value_lag1',
            'periods': -1,
            'groupColumns': ['nonexistent']
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("groupColumns 'nonexistent' does not exist.",
                      response_data['message'])

    def test_add_lag_lead_column_existing_column_name(self):
        # 既存の列名を新しい列名として指定
        payload = {
            'tableName': 'TestTable',
            'sourceColumn': 'value',
            'newColumnName': 'group',  # 既存の列名
            'periods': -1,
            'groupColumns': []
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("newColumnName 'group' already exists.",
                      response_data['message'])

    def test_add_lag_lead_column_multiple_periods(self):
        # 複数期間のラグを追加
        payload = {
            'tableName': 'TestTable',
            'sourceColumn': 'value',
            'newColumnName': 'value_lag2',
            'periods': -2,
            'groupColumns': []
        }
        response = self.client.post(
            '/api/add-lag-lead-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # 2期間ラグが正しく追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('value_lag2', df.columns)
        lag_values = df['value_lag2'].to_list()
        # 最初の2つの値はNone
        expected = [None, None, 10, 20, 30, 40]
        self.assertEqual(lag_values, expected)
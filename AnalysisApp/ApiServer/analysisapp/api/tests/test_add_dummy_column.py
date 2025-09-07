from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json

from ..apis.data.tables_manager import TablesManager


class TestApiAddDummyColumn(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'gender': ['male', 'female', 'female', 'male', 'other'],
            'age': [25, 30, 35, 40, 28]
        })
        self.tables_manager.store_table('TestTable', df)

    def test_add_dummy_column_success(self):
        # 正常にダミー変数列を追加できる
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'gender',
            'dummyColumnName': 'is_female',
            'targetValue': 'female'
        }
        response = self.client.post(
            '/api/add-dummy-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'TestTable')
        self.assertEqual(response_data['result']['dummyColumnName'], 'is_female')
        
        # ダミー変数列が正しく作成されているかチェック
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('is_female', df.columns)
        # femaleの値が1、それ以外が0になっているかチェック
        expected_values = [0, 1, 1, 0, 0]  # male, female, female, male, other
        self.assertEqual(df['is_female'].to_list(), expected_values)

    def test_add_dummy_column_invalid_table(self):
        # 存在しないテーブル名
        payload = {
            'tableName': 'NoTable',
            'sourceColumnName': 'gender',
            'dummyColumnName': 'is_female',
            'targetValue': 'female'
        }
        response = self.client.post(
            '/api/add-dummy-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn('NoTable', response_data['message'])
        self.assertIn('does not exist', response_data['message'])

    def test_add_dummy_column_invalid_source_column(self):
        # 存在しないソース列名を指定
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'invalid_column',
            'dummyColumnName': 'is_female',
            'targetValue': 'female'
        }
        response = self.client.post(
            '/api/add-dummy-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn('invalid_column', response_data['message'])
        self.assertIn('does not exist', response_data['message'])

    def test_add_dummy_column_duplicate_column_name(self):
        # 既存の列名をダミー列名として指定
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'gender',
            'dummyColumnName': 'age',  # 既存の列名
            'targetValue': 'female'
        }
        response = self.client.post(
            '/api/add-dummy-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn('age', response_data['message'])
        
    def test_add_dummy_column_with_numeric_target(self):
        # 数値のターゲット値でダミー変数を作成
        # 新しいテーブルを作成
        df_numeric = pl.DataFrame({
            'score': [85, 90, 75, 90, 88],
            'name': ['A', 'B', 'C', 'D', 'E']
        })
        self.tables_manager.store_table('NumericTable', df_numeric)
        
        payload = {
            'tableName': 'NumericTable',
            'sourceColumnName': 'score',
            'dummyColumnName': 'is_excellent',
            'targetValue': '90'
        }
        response = self.client.post(
            '/api/add-dummy-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # ダミー変数列が正しく作成されているかチェック
        df = self.tables_manager.get_table('NumericTable').table
        expected_values = [0, 1, 0, 1, 0]  # 90の位置のみ1
        self.assertEqual(df['is_excellent'].to_list(), expected_values)
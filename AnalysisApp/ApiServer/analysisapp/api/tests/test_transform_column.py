from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json
import math

from ..apis.data.tables_manager import TablesManager


class TestApiTransformColumn(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 4, 8, 16],
            'B': [10, 20, 30, 40, 50],
            'C': [0.5, 1.0, 1.5, 2.0, 2.5]
        })
        self.tables_manager.store_table('TestTable', df)

    def test_transform_column_log_natural_success(self):
        # 自然対数変換のテスト
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_ln',
            'transformMethod': 'log'
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'TestTable')
        self.assertEqual(response_data['result']['columnName'], 'A_ln')

        # カラムが正しい位置に追加されているか
        df = self.tables_manager.get_table('TestTable').table
        expected_columns = ['A', 'A_ln', 'B', 'C']
        self.assertEqual(df.columns, expected_columns)

        # 自然対数の値が正しいか（近似値でチェック）
        ln_values = df['A_ln'].to_list()
        expected_ln_values = [math.log(1), math.log(2), math.log(4),
                              math.log(8), math.log(16)]
        for actual, expected in zip(ln_values, expected_ln_values):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_transform_column_log_base2_success(self):
        # 底2の対数変換のテスト
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_log2',
            'transformMethod': 'log',
            'logBase': 2
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # 底2の対数の値が正しいか
        df = self.tables_manager.get_table('TestTable').table
        log2_values = df['A_log2'].to_list()
        # log2(1), log2(2), log2(4), log2(8), log2(16)
        expected_log2_values = [0, 1, 2, 3, 4]
        for actual, expected in zip(log2_values, expected_log2_values):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_transform_column_power_square_success(self):
        # 二乗変換のテスト（デフォルト）
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_square',
            'transformMethod': 'power'
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # 二乗の値が正しいか
        df = self.tables_manager.get_table('TestTable').table
        square_values = df['A_square'].to_list()
        # 1^2, 2^2, 4^2, 8^2, 16^2
        expected_square_values = [1, 4, 16, 64, 256]
        self.assertEqual(square_values, expected_square_values)

    def test_transform_column_power_cube_success(self):
        # 三乗変換のテスト
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_cube',
            'transformMethod': 'power',
            'exponent': 3
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # 三乗の値が正しいか
        df = self.tables_manager.get_table('TestTable').table
        cube_values = df['A_cube'].to_list()
        # 1^3, 2^3, 4^3, 8^3, 16^3
        expected_cube_values = [1, 8, 64, 512, 4096]
        self.assertEqual(cube_values, expected_cube_values)

    def test_transform_column_invalid_table(self):
        # 存在しないテーブル名
        payload = {
            'tableName': 'NoTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_ln',
            'transformMethod': 'log'
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NoTable' does not exist",
                      response_data['message'])

    def test_transform_column_invalid_source_column(self):
        # 存在しないソースカラム名
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'Z',
            'newColumnName': 'Z_ln',
            'transformMethod': 'log'
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "sourceColumnName 'Z' does not exist.")

    def test_transform_column_duplicate_column_name(self):
        # 既存のカラム名と重複
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'B',  # 既存のカラム名
            'transformMethod': 'log'
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertEqual(response_data['message'],
                         "newColumnName 'B' already exists.")

    def test_transform_column_invalid_method(self):
        # 無効な変換方法
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_invalid',
            'transformMethod': 'invalid'
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("transformMethod 'invalid' is invalid",
                      response_data['message'])

    def test_transform_column_invalid_log_base(self):
        # 無効な対数の底
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_log',
            'transformMethod': 'log',
            'logBase': 1  # 無効：底が1
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("logBase must be a positive number not equal to 1",
                      response_data['message'])

    def test_transform_column_negative_log_base(self):
        # 負の対数の底
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_log',
            'transformMethod': 'log',
            'logBase': -2  # 無効：負の値
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("logBase must be a positive number not equal to 1",
                      response_data['message'])

    def test_transform_column_fractional_exponent(self):
        # 小数の指数での累乗変換
        payload = {
            'tableName': 'TestTable',
            'sourceColumnName': 'A',
            'newColumnName': 'A_sqrt',
            'transformMethod': 'power',
            'exponent': 0.5  # 平方根
        }
        response = self.client.post(
            '/api/transform-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # 平方根の値が正しいか
        df = self.tables_manager.get_table('TestTable').table
        sqrt_values = df['A_sqrt'].to_list()
        expected_sqrt_values = [1.0, math.sqrt(2), 2.0, math.sqrt(8), 4.0]
        for actual, expected in zip(sqrt_values, expected_sqrt_values):
            self.assertAlmostEqual(actual, expected, places=5)

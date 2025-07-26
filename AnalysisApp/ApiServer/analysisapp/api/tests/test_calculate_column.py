from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json

from ..apis.data.tables_manager import TablesManager


class TestApiCalculateColumn(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': [10.0, 20.0, 30.0],
            'D': [2.5, 3.5, 4.5],
            'text_col': ['hello', 'world', 'test']  # 非数値列
        })
        self.tables_manager.store_table('TestTable', df)

    def test_calculate_column_simple_addition(self):
        # 単純な足し算
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'E',
            'calculationExpression': '<A> + <B>'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'TestTable')
        self.assertEqual(response_data['result']['columnName'], 'E')
        
        # 計算結果の確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertTrue('E' in df.columns)
        expected_values = [5, 7, 9]  # [1+4, 2+5, 3+6]
        self.assertEqual(df['E'].to_list(), expected_values)

    def test_calculate_column_complex_expression(self):
        # 複雑な計算式（四則演算とかっこ）
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'F',
            'calculationExpression': '<C>/<D>+(<A> + <B>)*2'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # 計算結果の確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertTrue('F' in df.columns)
        # 期待値: 10.0/2.5+(1+4)*2=4+10=14, 20.0/3.5+(2+5)*2=5.714...+14=19.714..., 30.0/4.5+(3+6)*2=6.666...+18=24.666...
        result_values = df['F'].to_list()
        self.assertAlmostEqual(result_values[0], 14.0, places=5)
        self.assertAlmostEqual(result_values[1], 19.714285714285715, places=5)
        self.assertAlmostEqual(result_values[2], 24.666666666666668, places=5)

    def test_calculate_column_with_numbers(self):
        # 列と数値の計算
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'G',
            'calculationExpression': '<A> * 5 + 10'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 計算結果の確認
        df = self.tables_manager.get_table('TestTable').table
        expected_values = [15, 20, 25]  # [1*5+10, 2*5+10, 3*5+10]
        self.assertEqual(df['G'].to_list(), expected_values)

    def test_calculate_column_invalid_table(self):
        # 存在しないテーブル名
        payload = {
            'tableName': 'NoTable',
            'newColumnName': 'E',
            'calculationExpression': '<A> + <B>'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NoTable' does not exist", 
                      response_data['message'])

    def test_calculate_column_invalid_column(self):
        # 存在しない列名を参照
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'E',
            'calculationExpression': '<A> + <Z>'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Column 'Z' does not exist", response_data['message'])

    def test_calculate_column_non_numeric_column(self):
        # 非数値列を参照
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'E',
            'calculationExpression': '<A> + <text_col>'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Column 'text_col' is not numeric", 
                      response_data['message'])

    def test_calculate_column_empty_expression(self):
        # 空の計算式
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'E',
            'calculationExpression': ''
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Calculation expression cannot be empty", 
                      response_data['message'])

    def test_calculate_column_no_column_reference(self):
        # 列参照がない計算式
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'E',
            'calculationExpression': '5 + 10'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("must reference at least one column", 
                      response_data['message'])

    def test_calculate_column_duplicate_column_name(self):
        # 既存の列名と同じ新列名
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'A',  # 既存の列名
            'calculationExpression': '<B> + <C>'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("newColumnName 'A' already exists", 
                      response_data['message'])

    def test_calculate_column_invalid_syntax(self):
        # 不正な計算式
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'E',
            'calculationExpression': '<A> @ <B>'  # 不正な演算子
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Invalid calculation expression", 
                      response_data['message'])

    def test_calculate_column_division_by_zero_handling(self):
        # ゼロ除算のテスト
        # ゼロを含むテーブルを作成
        df_zero = pl.DataFrame({
            'X': [1, 2, 0],
            'Y': [0, 2, 1]
        })
        self.tables_manager.store_table('ZeroTable', df_zero)
        
        payload = {
            'tableName': 'ZeroTable',
            'newColumnName': 'Z',
            'calculationExpression': '<X> / <Y>'
        }
        response = self.client.post(
            '/api/calculate-column',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # ゼロ除算の結果を確認（Polarsはinfまたはnullを返す）
        df = self.tables_manager.get_table('ZeroTable').table
        result_values = df['Z'].to_list()
        # 1/0 = inf, 2/2 = 1.0, 0/1 = 0.0
        import math
        self.assertTrue(math.isinf(result_values[0]))
        self.assertEqual(result_values[1], 1.0)
        self.assertEqual(result_values[2], 0.0)
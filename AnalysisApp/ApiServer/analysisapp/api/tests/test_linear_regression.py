from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json
import numpy as np

from ..apis.data.tables_manager import TablesManager


class TestApiLinearRegression(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()

        # 線形回帰分析用テストデータを作成
        # 連続値の被説明変数と複数の説明変数を持つテーブル
        np.random.seed(42)  # 再現可能な結果のため
        n_samples = 100

        # 説明変数の生成
        x1 = np.random.normal(0, 1, n_samples)
        x2 = np.random.normal(0, 1, n_samples)
        x3 = np.random.uniform(0, 10, n_samples)

        # 線形関数を使用して被説明変数を生成 (y = β₀ + β₁x₁ + β₂x₂ + β₃x₃ + ε)
        y = 2.5 + 0.5 * x1 + 1.2 * x2 + 0.1 * x3 + np.random.normal(0, 0.5,
                                                                    n_samples)

        df = pl.DataFrame({
            'y': y,
            'x1': x1,
            'x2': x2,
            'x3': x3,
            'id': range(n_samples)
        })
        self.tables_manager.store_table('LinearTestTable', df)

        # 数値以外のデータを含むテーブル（エラーテスト用）
        df_with_text = pl.DataFrame({
            'y': [1.0, 2.0, 3.0, 4.0],
            'x1': [1.0, 2.0, 3.0, 4.0],
            'text_col': ['a', 'b', 'c', 'd']
        })
        self.tables_manager.store_table('TextTable', df_with_text)

    def test_linear_regression_success(self):
        """正常に線形回帰分析が実行できる"""
        payload = {
            'tableName': 'LinearTestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2']
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # 結果の構造をチェック
        result = response_data['result']
        self.assertIn('tableName', result)
        self.assertIn('dependentVariable', result)
        self.assertIn('explanatoryVariables', result)
        self.assertIn('regressionResult', result)
        self.assertIn('parameters', result)
        self.assertIn('modelStatistics', result)

        # パラメータの構造をチェック
        parameters = result['parameters']
        self.assertIsInstance(parameters, list)
        self.assertEqual(len(parameters), 3)  # const + x1 + x2

        # 各パラメータに必要な情報があることを確認
        for param in parameters:
            self.assertIn('variable', param)
            self.assertIn('coefficient', param)
            self.assertIn('pValue', param)
            self.assertIn('tValue', param)

        # モデル統計情報をチェック
        stats = result['modelStatistics']
        self.assertIn('R2', stats)
        self.assertIn('adjustedR2', stats)
        self.assertIn('fValue', stats)
        self.assertIn('fProbability', stats)
        self.assertIn('logLikelihood', stats)
        self.assertIn('nObservations', stats)

    def test_linear_regression_multiple_variables(self):
        """複数の説明変数で線形回帰分析が実行できる"""
        payload = {
            'tableName': 'LinearTestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2', 'x3']
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # パラメータ数をチェック（定数項 + 3つの説明変数）
        result = response_data['result']
        parameters = result['parameters']
        self.assertEqual(len(parameters), 4)

    def test_linear_regression_invalid_table(self):
        """存在しないテーブル名でエラーが返される"""
        payload = {
            'tableName': 'NonExistentTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2']
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NonExistentTable' does not exist",
                      response_data['message'])

    def test_linear_regression_invalid_dependent_variable(self):
        """存在しない被説明変数でエラーが返される"""
        payload = {
            'tableName': 'LinearTestTable',
            'dependentVariable': 'nonexistent_y',
            'explanatoryVariables': ['x1', 'x2']
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("dependentVariable 'nonexistent_y' does not exist",
                      response_data['message'])

    def test_linear_regression_invalid_explanatory_variable(self):
        """存在しない説明変数でエラーが返される"""
        payload = {
            'tableName': 'LinearTestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'nonexistent_x']
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("explanatoryVariables 'nonexistent_x' does not exist",
                      response_data['message'])

    def test_linear_regression_empty_explanatory_variables(self):
        """説明変数が空の場合エラーが返される"""
        payload = {
            'tableName': 'LinearTestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': []
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("explanatoryVariables must be with "
                      "at least one explanatory_variable.",
                      response_data['message'])

    def test_linear_regression_dependent_in_explanatory(self):
        """被説明変数が説明変数に含まれている場合エラーが返される"""
        payload = {
            'tableName': 'LinearTestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'y', 'x2']
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Dependent variable cannot be "
                      "included in explanatory variables",
                      response_data['message'])

    def test_linear_regression_missing_parameters(self):
        """必須パラメータが不足している場合エラーが返される"""
        # tableName がない場合
        payload = {
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2']
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Required parameter is missing",
                      response_data['message'])

    def test_linear_regression_single_explanatory_variable(self):
        """単一の説明変数でも線形回帰分析が実行できる"""
        payload = {
            'tableName': 'LinearTestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1']
        }
        response = self.client.post(
            '/api/linear-regression',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # パラメータ数をチェック（定数項 + 1つの説明変数）
        result = response_data['result']
        parameters = result['parameters']
        self.assertEqual(len(parameters), 2)

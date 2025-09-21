from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json
import numpy as np

from ..apis.data.tables_manager import TablesManager


class TestApiVariableEffectsEstimation(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()

        # 変量効果推定分析用テストデータを作成
        np.random.seed(42)  # 再現可能な結果のため
        n_samples = 100

        # 説明変数の生成
        x1 = np.random.normal(0, 1, n_samples)
        x2 = np.random.normal(0, 1, n_samples)
        x3 = np.random.uniform(0, 10, n_samples)

        # 被説明変数の生成（線形関係）
        y = 2.0 + 1.5 * x1 + 0.8 * x2 + 0.2 * x3 + np.random.normal(0, 0.5, n_samples)

        df = pl.DataFrame({
            'y': y,
            'x1': x1,
            'x2': x2,
            'x3': x3,
            'id': range(n_samples)
        })
        self.tables_manager.store_table('VEETestTable', df)

        # 数値以外のデータを含むテーブル（エラーテスト用）
        df_with_text = pl.DataFrame({
            'y': [1.0, 2.0, 3.0, 4.0],
            'x1': [1.0, 2.0, 3.0, 4.0],
            'text_col': ['a', 'b', 'c', 'd']
        })
        self.tables_manager.store_table('TextTable', df_with_text)

    def test_variable_effects_estimation_success_default(self):
        """デフォルト設定で正常に変量効果推定分析が実行できる"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2']
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
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
        self.assertIn('standardErrorMethod', result)
        self.assertIn('useTDistribution', result)
        self.assertIn('regressionResult', result)
        self.assertIn('parameters', result)
        self.assertIn('modelStatistics', result)

        # デフォルト値をチェック
        self.assertEqual(result['standardErrorMethod'], 'nonrobust')
        self.assertEqual(result['useTDistribution'], True)

        # パラメータの構造をチェック
        parameters = result['parameters']
        self.assertIsInstance(parameters, list)
        self.assertEqual(len(parameters), 3)  # const + x1 + x2

        # 各パラメータに必要な情報があることを確認
        for param in parameters:
            self.assertIn('variable', param)
            self.assertIn('coefficient', param)
            self.assertIn('standardError', param)
            self.assertIn('pValue', param)
            self.assertIn('tValue', param)
            self.assertIn('confidenceIntervalLower', param)
            self.assertIn('confidenceIntervalUpper', param)

        # モデル統計情報をチェック
        stats = result['modelStatistics']
        expected_stats = ['R2', 'adjustedR2', 'AIC', 'BIC', 'fValue', 
                         'fProbability', 'logLikelihood', 'nObservations',
                         'degreesOfFreedom', 'residualDegreesOfFreedom']
        for stat in expected_stats:
            self.assertIn(stat, stats)

    def test_variable_effects_estimation_hc1_robust(self):
        """HC1標準誤差で変量効果推定分析が実行できる"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2', 'x3'],
            'standardErrorMethod': 'HC1',
            'useTDistribution': False
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['standardErrorMethod'], 'HC1')
        self.assertEqual(result['useTDistribution'], False)

        # パラメータ数をチェック（定数項 + 3つの説明変数）
        parameters = result['parameters']
        self.assertEqual(len(parameters), 4)

    def test_variable_effects_estimation_hac(self):
        """HAC標準誤差で変量効果推定分析が実行できる"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'standardErrorMethod': 'HAC',
            'useTDistribution': True
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['standardErrorMethod'], 'HAC')
        self.assertEqual(result['useTDistribution'], True)

    def test_variable_effects_estimation_invalid_table(self):
        """存在しないテーブル名でエラーが返される"""
        payload = {
            'tableName': 'NonExistentTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2']
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NonExistentTable' does not exist",
                      response_data['message'])

    def test_variable_effects_estimation_invalid_dependent_variable(self):
        """存在しない被説明変数でエラーが返される"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'nonexistent_y',
            'explanatoryVariables': ['x1', 'x2']
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("dependentVariable 'nonexistent_y' does not exist",
                      response_data['message'])

    def test_variable_effects_estimation_invalid_explanatory_variable(self):
        """存在しない説明変数でエラーが返される"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'nonexistent_x']
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("explanatoryVariables 'nonexistent_x' does not exist",
                      response_data['message'])

    def test_variable_effects_estimation_empty_explanatory_variables(self):
        """説明変数が空の場合エラーが返される"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': []
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("explanatoryVariables must be with "
                      "at least 1 explanatory_variable.",
                      response_data['message'])

    def test_variable_effects_estimation_dependent_in_explanatory(self):
        """被説明変数が説明変数に含まれている場合エラーが返される"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'y', 'x2']
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Dependent variable cannot be "
                      "included in explanatory variables",
                      response_data['message'])

    def test_variable_effects_estimation_invalid_standard_error_method(self):
        """不正な標準誤差計算方法でエラーが返される"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2'],
            'standardErrorMethod': 'invalid_method'
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("standardErrorMethod must be one of:",
                      response_data['message'])

    def test_variable_effects_estimation_missing_parameters(self):
        """必須パラメータが不足している場合エラーが返される"""
        # tableName がない場合
        payload = {
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2']
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Required parameter is missing",
                      response_data['message'])

    def test_variable_effects_estimation_all_standard_error_methods(self):
        """全ての標準誤差計算方法が正常に動作する"""
        supported_methods = ['nonrobust', 'HC0', 'HC1', 'HC2', 'HC3', 'HAC']
        
        for method in supported_methods:
            with self.subTest(method=method):
                payload = {
                    'tableName': 'VEETestTable',
                    'dependentVariable': 'y',
                    'explanatoryVariables': ['x1'],
                    'standardErrorMethod': method,
                    'useTDistribution': True
                }
                response = self.client.post(
                    '/api/variable-effects-estimation',
                    data=json.dumps(payload),
                    content_type='application/json'
                )

                response_data = response.json()
                self.assertEqual(response.status_code, status.HTTP_200_OK, 
                               f"Failed for method: {method}")
                self.assertEqual(response_data['code'], 'OK')
                
                result = response_data['result']
                self.assertEqual(result['standardErrorMethod'], method)

    def test_variable_effects_estimation_single_explanatory_variable(self):
        """単一の説明変数でも変量効果推定分析が実行できる"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'standardErrorMethod': 'HC2',
            'useTDistribution': False
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
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

    def test_variable_effects_estimation_confidence_intervals(self):
        """信頼区間が正しく計算される"""
        payload = {
            'tableName': 'VEETestTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2'],
            'standardErrorMethod': 'HC1',
            'useTDistribution': True
        }
        response = self.client.post(
            '/api/variable-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        result = response_data['result']
        parameters = result['parameters']
        
        # 各パラメータの信頼区間をチェック
        for param in parameters:
            lower = param['confidenceIntervalLower']
            upper = param['confidenceIntervalUpper']
            coefficient = param['coefficient']
            
            # 信頼区間の論理的な順序をチェック
            self.assertLess(lower, upper)
            # 係数は信頼区間内にある（通常95%信頼区間）
            self.assertLessEqual(lower, coefficient)
            self.assertLessEqual(coefficient, upper)
from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json
import numpy as np

from ..apis.data.tables_manager import TablesManager


class TestApiAddSimulationColumn(APITestCase):
    
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10, 20, 30, 40, 50]
        })
        self.tables_manager.store_table('TestTable', df)
        
    def test_add_uniform_column_success(self):
        """一様分布の列追加が正常に動作することをテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'UniformCol',
            'distributionType': 'uniform',
            'distributionParams': {
                'low': 0.0,
                'high': 1.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'TestTable')
        self.assertEqual(response_data['result']['columnName'], 'UniformCol')
        self.assertEqual(response_data['result']['distributionType'], 'uniform')
        
        # データが追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('UniformCol', df.columns)
        uniform_values = df['UniformCol'].to_list()
        self.assertEqual(len(uniform_values), 5)
        # 一様分布の範囲内にあることを確認
        self.assertTrue(all(0.0 <= val <= 1.0 for val in uniform_values))
        
    def test_add_normal_column_success(self):
        """正規分布の列追加が正常に動作することをテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'NormalCol',
            'distributionType': 'normal',
            'distributionParams': {
                'loc': 0.0,
                'scale': 1.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # データが追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('NormalCol', df.columns)
        normal_values = df['NormalCol'].to_list()
        self.assertEqual(len(normal_values), 5)
        
    def test_add_binomial_column_success(self):
        """二項分布の列追加が正常に動作することをテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'BinomialCol',
            'distributionType': 'binomial',
            'distributionParams': {
                'n': 10,
                'p': 0.5
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # データが追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('BinomialCol', df.columns)
        binomial_values = df['BinomialCol'].to_list()
        self.assertEqual(len(binomial_values), 5)
        # 二項分布の範囲内にあることを確認
        self.assertTrue(all(0 <= val <= 10 for val in binomial_values))
        
    def test_add_exponential_column_success(self):
        """指数分布の列追加が正常に動作することをテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'ExponentialCol',
            'distributionType': 'exponential',
            'distributionParams': {
                'scale': 1.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
        # データが追加されているか確認
        df = self.tables_manager.get_table('TestTable').table
        self.assertIn('ExponentialCol', df.columns)
        exp_values = df['ExponentialCol'].to_list()
        self.assertEqual(len(exp_values), 5)
        # 指数分布は非負の値
        self.assertTrue(all(val >= 0 for val in exp_values))
        
    def test_add_gamma_column_success(self):
        """ガンマ分布の列追加が正常に動作することをテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'GammaCol',
            'distributionType': 'gamma',
            'distributionParams': {
                'shape': 2.0,
                'scale': 1.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_add_beta_column_success(self):
        """ベータ分布の列追加が正常に動作することをテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'BetaCol',
            'distributionType': 'beta',
            'distributionParams': {
                'a': 2.0,
                'b': 5.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # ベータ分布は[0,1]の範囲
        df = self.tables_manager.get_table('TestTable').table
        beta_values = df['BetaCol'].to_list()
        self.assertTrue(all(0 <= val <= 1 for val in beta_values))
        
    def test_add_poisson_column_success(self):
        """ポアソン分布の列追加が正常に動作することをテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'PoissonCol',
            'distributionType': 'poisson',
            'distributionParams': {
                'lam': 3.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # ポアソン分布は非負の整数
        df = self.tables_manager.get_table('TestTable').table
        poisson_values = df['PoissonCol'].to_list()
        self.assertTrue(all(val >= 0 for val in poisson_values))
        
    def test_invalid_table_name(self):
        """存在しないテーブル名を指定した場合のテスト"""
        payload = {
            'tableName': 'NoTable',
            'newColumnName': 'SimCol',
            'distributionType': 'normal',
            'distributionParams': {
                'loc': 0.0,
                'scale': 1.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NoTable' does not exist", response_data['message'])
        
    def test_duplicate_column_name(self):
        """既存の列名と同じ名前を指定した場合のテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'A',  # 既存の列名
            'distributionType': 'normal',
            'distributionParams': {
                'loc': 0.0,
                'scale': 1.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("newColumnName 'A' already exists", response_data['message'])
        
    def test_unsupported_distribution(self):
        """サポートされていない分布を指定した場合のテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'TestCol',
            'distributionType': 'unsupported',
            'distributionParams': {}
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("distributionType 'unsupported' is not supported", response_data['message'])
        
    def test_invalid_uniform_params(self):
        """一様分布の無効なパラメータを指定した場合のテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'TestCol',
            'distributionType': 'uniform',
            'distributionParams': {
                'low': 1.0,
                'high': 0.0  # lowより小さい
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("'low' must be less than 'high'", response_data['message'])
        
    def test_missing_required_params(self):
        """必要なパラメータが不足している場合のテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'TestCol',
            'distributionType': 'normal',
            'distributionParams': {
                'loc': 0.0
                # scaleが不足
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Missing required parameter for normal distribution: 'scale'", response_data['message'])
        
    def test_invalid_param_type(self):
        """パラメータの型が不正な場合のテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'TestCol',
            'distributionType': 'normal',
            'distributionParams': {
                'loc': 'invalid',  # 文字列は無効
                'scale': 1.0
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Parameter 'loc' must be a number", response_data['message'])
        
    def test_negative_scale_normal(self):
        """正規分布で負のscaleを指定した場合のテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'TestCol',
            'distributionType': 'normal',
            'distributionParams': {
                'loc': 0.0,
                'scale': -1.0  # 負の値は無効
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("'scale' must be positive", response_data['message'])
        
    def test_binomial_invalid_p(self):
        """二項分布で無効なpを指定した場合のテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'TestCol',
            'distributionType': 'binomial',
            'distributionParams': {
                'n': 10,
                'p': 1.5  # 1より大きい
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("'p' must be between 0 and 1", response_data['message'])
        
    def test_hypergeometric_success(self):
        """超幾何分布の列追加が正常に動作することをテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'HyperGeomCol',
            'distributionType': 'hypergeometric',
            'distributionParams': {
                'N': 100,
                'K': 30,
                'n': 10
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        
    def test_hypergeometric_invalid_params(self):
        """超幾何分布で無効なパラメータを指定した場合のテスト"""
        payload = {
            'tableName': 'TestTable',
            'newColumnName': 'TestCol',
            'distributionType': 'hypergeometric',
            'distributionParams': {
                'N': 10,
                'K': 15,  # NよりKが大きい
                'n': 5
            }
        }
        response = self.client.post(
            '/api/add-simulation-column',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("'K' must not exceed 'N'", response_data['message'])
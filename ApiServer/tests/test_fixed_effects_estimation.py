import json

import numpy as np
import polars as pl
from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestApiFixedEffectsEstimation(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()

        # 固定効果分析用テストデータを作成
        # パネルデータ（個体×時点の構造）
        np.random.seed(42)  # 再現可能な結果のため
        n_entities = 10  # 個体数
        n_periods = 5    # 時点数
        n_total = n_entities * n_periods

        # 個体ID
        entity_ids = np.repeat(range(1, n_entities + 1), n_periods)

        # 時点ID
        time_ids = np.tile(range(1, n_periods + 1), n_entities)

        # 個体固有効果（時間不変）
        entity_effects = np.random.normal(0, 2, n_entities)
        entity_effects_expanded = np.repeat(entity_effects, n_periods)

        # 説明変数
        x1 = np.random.normal(0, 1, n_total)
        x2 = np.random.normal(0, 1, n_total)

        # 被説明変数（個体固有効果を含む）
        error = np.random.normal(0, 1, n_total)
        y = 2.0 + 1.5 * x1 + -0.8 * x2 + entity_effects_expanded + error

        df_panel = pl.DataFrame({
            'entity_id': entity_ids,
            'time_id': time_ids,
            'y': y,
            'x1': x1,
            'x2': x2
        })
        self.tables_manager.store_table('PanelData', df_panel)

        # 単一時点のデータ（エラーテスト用）
        df_single = pl.DataFrame({
            'entity_id': [1, 2, 3],
            'y': [1.0, 2.0, 3.0],
            'x1': [1.0, 2.0, 3.0]
        })
        self.tables_manager.store_table('SinglePeriod', df_single)

        # 数値以外のデータを含むテーブル（エラーテスト用）
        df_with_text = pl.DataFrame({
            'entity_id': [1, 1, 2, 2],
            'y': [1.0, 2.0, 3.0, 4.0],
            'x1': [1.0, 2.0, 3.0, 4.0],
            'text_col': ['a', 'b', 'c', 'd']
        })
        self.tables_manager.store_table('TextTable', df_with_text)

    def test_fixed_effects_estimation_success(self):
        """正常に固定効果推定が実行できる"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2'],
            'entityIdColumn': 'entity_id',
            'standardErrorMethod': 'normal',
            'useTDistribution': True
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
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
        self.assertIn('entityIdColumn', result)
        self.assertIn('estimationMethod', result)
        self.assertIn('regressionResult', result)
        self.assertIn('parameters', result)
        self.assertIn('modelStatistics', result)

        # パラメータの構造をチェック
        parameters = result['parameters']
        self.assertIsInstance(parameters, list)
        self.assertEqual(len(parameters), 2)  # x1 + x2

        # 各パラメータに必要な情報があることを確認
        for param in parameters:
            self.assertIn('variable', param)
            self.assertIn('coefficient', param)
            self.assertIn('pValue', param)
            self.assertIn('tValue', param)
            self.assertIn('standardError', param)

        # モデル統計情報をチェック
        stats = result['modelStatistics']
        self.assertIn('R2', stats)
        self.assertIn('adjustedR2', stats)
        self.assertIn('nObservations', stats)
        self.assertIn('nEntities', stats)
        self.assertIn('standardErrorMethod', stats)
        self.assertIn('useTDistribution', stats)

        # 推定結果の妥当性をチェック（真の係数に近いか）
        x1_coeff = next(
            p['coefficient'] for p in parameters if p['variable'] == 'x1')
        x2_coeff = next(
            p['coefficient'] for p in parameters if p['variable'] == 'x2')

        # 真の係数: x1=1.5, x2=-0.8 に対する許容範囲
        self.assertAlmostEqual(x1_coeff, 1.5, delta=0.5)
        self.assertAlmostEqual(x2_coeff, -0.8, delta=0.5)

    def test_fixed_effects_estimation_robust_standard_errors(self):
        """頑健な標準誤差で固定効果推定が実行できる"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'entity_id',
            'standardErrorMethod': 'robust',
            'useTDistribution': False
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['modelStatistics']['standardErrorMethod'],
                         'robust')
        self.assertEqual(result['modelStatistics']['useTDistribution'], False)

    def test_fixed_effects_estimation_clustered_standard_errors(self):
        """クラスター標準誤差で固定効果推定が実行できる"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'entity_id',
            'standardErrorMethod': 'clustered',
            'useTDistribution': True
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['modelStatistics']['standardErrorMethod'],
                         'clustered')

    def test_fixed_effects_estimation_hac_standard_errors(self):
        """HAC標準誤差で固定効果推定が実行できる"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'entity_id',
            'standardErrorMethod': 'hac',
            'useTDistribution': True
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['modelStatistics']['standardErrorMethod'],
                         'hac')

    def test_fixed_effects_estimation_invalid_table(self):
        """存在しないテーブル名でエラーが返される"""
        payload = {
            'tableName': 'NonExistentTable',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NonExistentTable' does not exist",
                      response_data['message'])

    def test_fixed_effects_estimation_invalid_dependent_variable(self):
        """存在しない被説明変数でエラーが返される"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'nonexistent_y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("dependentVariable 'nonexistent_y' does not exist",
                      response_data['message'])

    def test_fixed_effects_estimation_invalid_explanatory_variable(self):
        """存在しない説明変数でエラーが返される"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'nonexistent_x'],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("explanatoryVariables 'nonexistent_x' does not exist",
                      response_data['message'])

    def test_fixed_effects_estimation_invalid_entity_id_column(self):
        """存在しない個体ID列でエラーが返される"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'nonexistent_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("entityIdColumn 'nonexistent_id' does not exist",
                      response_data['message'])

    def test_fixed_effects_estimation_entity_id_same_as_dependent(self):
        """個体ID列が被説明変数と同じ場合エラーが返される"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'y'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Entity ID column cannot be "
                      "the same as dependent variable",
                      response_data['message'])

    def test_fixed_effects_estimation_entity_id_in_explanatory(self):
        """個体ID列が説明変数に含まれている場合エラーが返される"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'entity_id'],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Entity ID column cannot be included in explanatory "
                      "variables",
                      response_data['message'])

    def test_fixed_effects_estimation_invalid_standard_error_method(self):
        """無効な標準誤差計算方法でエラーが返される"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'entity_id',
            'standardErrorMethod': 'invalid_method'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("is not supported. Supported standardErrorMethod:",
                      response_data['message'])

    def test_fixed_effects_estimation_single_period_data(self):
        """単一時点のデータでエラーが返される"""
        payload = {
            'tableName': 'SinglePeriod',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("No entities with multiple observations found",
                      response_data['message'])

    def test_fixed_effects_estimation_empty_explanatory_variables(self):
        """説明変数が空の場合エラーが返される"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': [],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("explanatoryVariables must be with "
                      "at least 1 explanatory_variable.",
                      response_data['message'])

    def test_fixed_effects_estimation_dependent_in_explanatory(self):
        """被説明変数が説明変数に含まれている場合エラーが返される"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'y'],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Dependent variable cannot be "
                      "included in explanatory variables",
                      response_data['message'])

    def test_fixed_effects_estimation_missing_required_parameters(self):
        """必須パラメータが不足している場合エラーが返される"""
        # entityIdColumn がない場合
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1']
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Required parameter is missing",
                      response_data['message'])

    def test_fixed_effects_estimation_single_explanatory_variable(self):
        """単一の説明変数でも固定効果推定が実行できる"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1'],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # パラメータ数をチェック（1つの説明変数のみ）
        result = response_data['result']
        parameters = result['parameters']
        self.assertEqual(len(parameters), 1)
        self.assertEqual(parameters[0]['variable'], 'x1')

    def test_fixed_effects_estimation_with_default_parameters(self):
        """デフォルトパラメータで固定効果推定が実行できる"""
        payload = {
            'tableName': 'PanelData',
            'dependentVariable': 'y',
            'explanatoryVariables': ['x1', 'x2'],
            'entityIdColumn': 'entity_id'
        }
        response = self.client.post(
            '/api/fixed-effects-estimation',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        stats = result['modelStatistics']
        # デフォルト値の確認
        self.assertEqual(stats['standardErrorMethod'], 'normal')
        self.assertEqual(stats['useTDistribution'], True)

from rest_framework.test import APITestCase
from rest_framework import status
import polars as pl
import json
import numpy as np

from ..apis.data.tables_manager import TablesManager


class TestApiConfidenceInterval(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # テーブルをクリア
        self.tables_manager.clear_tables()

        # 信頼区間計算用テストデータを作成
        np.random.seed(42)  # 再現可能な結果のため
        n_samples = 100

        # 正規分布に従うデータ
        normal_data = np.random.normal(50, 10, n_samples)

        # 二項データ（0または1）
        binary_data = np.random.binomial(1, 0.3, n_samples)

        # テストテーブルの作成
        df = pl.DataFrame({
            'normal_col': normal_data,
            'binary_col': binary_data,
            'id': range(n_samples)
        })
        self.tables_manager.store_table('ConfidenceTestTable', df)

        # 数値以外のデータを含むテーブル（エラーテスト用）
        df_with_text = pl.DataFrame({
            'numeric_col': [1.0, 2.0, 3.0, 4.0],
            'text_col': ['a', 'b', 'c', 'd']
        })
        self.tables_manager.store_table('TextTable', df_with_text)

        # 空データテーブル
        df_empty = pl.DataFrame({
            'empty_col': [None, None, None]
        })
        self.tables_manager.store_table('EmptyTable', df_empty)

    def test_confidence_interval_mean_success(self):
        """平均値の信頼区間計算が正常に動作する"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': 0.95,
            'statisticType': 'mean'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        # 結果の構造をチェック
        result = response_data['result']
        self.assertIn('tableName', result)
        self.assertIn('columnName', result)
        self.assertIn('statistic', result)
        self.assertIn('confidence_interval', result)
        self.assertIn('confidence_level', result)

        # 統計量の構造をチェック
        statistic = result['statistic']
        self.assertEqual(statistic['type'], 'mean')
        self.assertIsInstance(statistic['value'], (int, float))

        # 信頼区間の構造をチェック
        ci = result['confidence_interval']
        self.assertIn('lower', ci)
        self.assertIn('upper', ci)
        self.assertIsInstance(ci['lower'], (int, float))
        self.assertIsInstance(ci['upper'], (int, float))
        self.assertLess(ci['lower'], ci['upper'])

        # 信頼度レベルのチェック
        self.assertEqual(result['confidence_level'], 0.95)
        self.assertEqual(result['columnName'], 'normal_col')

    def test_confidence_interval_median_success(self):
        """中央値の信頼区間計算が正常に動作する"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': 0.90,
            'statisticType': 'median'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['statistic']['type'], 'median')
        self.assertEqual(result['confidence_level'], 0.90)

    def test_confidence_interval_proportion_success(self):
        """比率の信頼区間計算が正常に動作する"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'binary_col',
            'confidenceLevel': 0.95,
            'statisticType': 'proportion'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['statistic']['type'], 'proportion')

        # 比率は0から1の間でなければならない
        proportion_value = result['statistic']['value']
        self.assertGreaterEqual(proportion_value, 0)
        self.assertLessEqual(proportion_value, 1)

        # 信頼区間も0から1の間
        ci = result['confidence_interval']
        self.assertGreaterEqual(ci['lower'], 0)
        self.assertLessEqual(ci['upper'], 1)

    def test_confidence_interval_variance_success(self):
        """分散の信頼区間計算が正常に動作する"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': 0.95,
            'statisticType': 'variance'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['statistic']['type'], 'variance')

        # 分散は正の値でなければならない
        variance_value = result['statistic']['value']
        self.assertGreater(variance_value, 0)

    def test_confidence_interval_std_success(self):
        """標準偏差の信頼区間計算が正常に動作する"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': 0.95,
            'statisticType': 'std'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['statistic']['type'], 'std')

        # 標準偏差は正の値でなければならない
        std_value = result['statistic']['value']
        self.assertGreater(std_value, 0)

    def test_confidence_interval_invalid_table(self):
        """存在しないテーブル名でエラーが返される"""
        payload = {
            'tableName': 'NonExistentTable',
            'columnName': 'normal_col',
            'confidenceLevel': 0.95,
            'statisticType': 'mean'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("tableName 'NonExistentTable' does not exist",
                      response_data['message'])

    def test_confidence_interval_invalid_column(self):
        """存在しない列名でエラーが返される"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'nonexistent_column',
            'confidenceLevel': 0.95,
            'statisticType': 'mean'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("columnName 'nonexistent_column' does not exist",
                      response_data['message'])

    def test_confidence_interval_invalid_statistic_type(self):
        """サポートされていない統計タイプでエラーが返される"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': 0.95,
            'statisticType': 'invalid_stat'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("statisticType 'invalid_stat' is not supported",
                      response_data['message'])

    def test_confidence_interval_invalid_confidence_level_high(self):
        """信頼度レベルが1以上の場合エラーが返される"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': 1.5,
            'statisticType': 'mean'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("confidenceLevel must be between 0 and 1",
                      response_data['message'])

    def test_confidence_interval_invalid_confidence_level_low(self):
        """信頼度レベルが0以下の場合エラーが返される"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': 0,
            'statisticType': 'mean'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("confidenceLevel must be between 0 and 1",
                      response_data['message'])

    def test_confidence_interval_proportion_invalid_data(self):
        """比率計算で0,1以外のデータがある場合エラーが返される"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',  # 0,1以外の値を含む列
            'confidenceLevel': 0.95,
            'statisticType': 'proportion'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("data must contain only 0 and 1 values",
                      response_data['message'])

    def test_confidence_interval_empty_data(self):
        """空データの場合エラーが返される"""
        payload = {
            'tableName': 'EmptyTable',
            'columnName': 'empty_col',
            'confidenceLevel': 0.95,
            'statisticType': 'mean'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Column contains no valid data",
                      response_data['message'])

    def test_confidence_interval_missing_parameters(self):
        """必須パラメータが不足している場合エラーが返される"""
        # tableName がない場合
        payload = {
            'columnName': 'normal_col',
            'confidenceLevel': 0.95,
            'statisticType': 'mean'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Required parameter is missing",
                      response_data['message'])

    def test_confidence_interval_different_levels(self):
        """異なる信頼度レベルでの計算が正常に動作する"""
        levels = [0.90, 0.95, 0.99]

        for level in levels:
            payload = {
                'tableName': 'ConfidenceTestTable',
                'columnName': 'normal_col',
                'confidenceLevel': level,
                'statisticType': 'mean'
            }
            response = self.client.post(
                '/api/confidence-interval',
                data=json.dumps(payload),
                content_type='application/json'
            )

            response_data = response.json()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response_data['code'], 'OK')

            result = response_data['result']
            self.assertEqual(result['confidence_level'], level)

            # より高い信頼度レベルはより広い区間になるはず
            if level == 0.99:
                ci_99 = result['confidence_interval']
            elif level == 0.95:
                ci_95 = result['confidence_interval']
            elif level == 0.90:
                ci_90 = result['confidence_interval']

        # 信頼区間の幅が信頼度レベルと正しい関係にあることを確認
        width_90 = ci_90['upper'] - ci_90['lower']
        width_95 = ci_95['upper'] - ci_95['lower']
        width_99 = ci_99['upper'] - ci_99['lower']

        self.assertLess(width_90, width_95)
        self.assertLess(width_95, width_99)

    def test_confidence_interval_json_structure_validation(self):
        """レスポンスのJSON構造が仕様通りである"""
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': 0.95,
            'statisticType': 'std'
        }
        response = self.client.post(
            '/api/confidence-interval',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response_data['result']

        # 必須フィールドの存在確認
        required_fields = ['tableName', 'columnName', 'statistic',
                          'confidence_interval', 'confidence_level']
        for field in required_fields:
            self.assertIn(field, result)

        # statisticの必須フィールド
        statistic = result['statistic']
        self.assertIn('type', statistic)
        self.assertIn('value', statistic)

        # confidence_intervalの必須フィールド
        ci = result['confidence_interval']
        self.assertIn('lower', ci)
        self.assertIn('upper', ci)

import json

from rest_framework import status
from rest_framework.test import APITestCase

from ..apis.data.tables_manager import TablesManager


class TestCreateSimulationDataTable(APITestCase):
    """CreateSimulationDataTableのテストクラス"""

    def setUp(self):
        self.tables_manager = TablesManager()
        # テスト前にテーブルをクリア
        self.tables_manager.clear_tables()

    def test_create_table_with_distribution_columns(self):
        """分布データ列を持つテーブル作成のテスト"""

        # テスト用の列設定
        column_settings = [
            {
                'columnName': 'normal_col',
                'dataType': 'distribution',
                'distributionType': 'normal',
                'distributionParams': {'loc': 0, 'scale': 1}
            },
            {
                'columnName': 'uniform_col',
                'dataType': 'distribution',
                'distributionType': 'uniform',
                'distributionParams': {'low': 0, 'high': 10}
            }
        ]
        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 100,
            'columnSettings': column_settings
        }
        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'test_table')

        # store_tableに渡されたDataFrameの確認
        self.assertIn('test_table', self.tables_manager.get_table_name_list())
        columns = self.tables_manager.get_column_name_list('test_table')
        self.assertIn('normal_col', columns)
        self.assertIn('uniform_col', columns)
        df = self.tables_manager.get_table('test_table').table
        self.assertEqual(len(columns), 2)
        self.assertEqual(len(df), 100)

    def test_create_table_with_fixed_columns(self):
        """固定値列を持つテーブル作成のテスト"""

        # テスト用の列設定
        column_settings = [
            {
                'columnName': 'fixed_col_1',
                'dataType': 'fixed',
                'fixedValue': 42
            },
            {
                'columnName': 'fixed_col_2',
                'dataType': 'fixed',
                'fixedValue': 'constant_string'
            }
        ]

        payload = {
            'tableName': 'fixed_table',
            'tableNumberOfRows': 50,
            'columnSettings': column_settings
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'fixed_table')

        # テーブルの確認
        self.assertIn('fixed_table', self.tables_manager.get_table_name_list())
        columns = self.tables_manager.get_column_name_list('fixed_table')
        self.assertIn('fixed_col_1', columns)
        self.assertIn('fixed_col_2', columns)
        df = self.tables_manager.get_table('fixed_table').table
        self.assertEqual(len(df), 50)

        # 固定値の確認
        self.assertTrue((df['fixed_col_1'] == 42).all())
        self.assertTrue((df['fixed_col_2'] == 'constant_string').all())

    def test_create_table_with_mixed_columns(self):
        """分布データ列と固定値列の混合テーブル作成のテスト"""

        # テスト用の列設定
        column_settings = [
            {
                'columnName': 'exponential_col',
                'dataType': 'distribution',
                'distributionType': 'exponential',
                'distributionParams': {'scale': 2.0}
            },
            {
                'columnName': 'fixed_id',
                'dataType': 'fixed',
                'fixedValue': 1
            }
        ]

        payload = {
            'tableName': 'mixed_table',
            'tableNumberOfRows': 30,
            'columnSettings': column_settings
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK
        self.assertEqual(response_data['code'], 'OK')
        self.assertEqual(response_data['result']['tableName'], 'mixed_table')

        # テーブルの確認
        self.assertIn('mixed_table', self.tables_manager.get_table_name_list())
        columns = self.tables_manager.get_column_name_list('mixed_table')
        self.assertIn('exponential_col', columns)
        self.assertIn('fixed_id', columns)
        df = self.tables_manager.get_table('mixed_table').table
        self.assertEqual(len(df), 30)
        self.assertEqual(len(df.columns), 2)

        # 固定値の確認
        self.assertTrue((df['fixed_id'] == 1).all())

    def test_validation_error_duplicate_table_name(self):
        """重複するテーブル名のバリデーションエラーテスト"""

        # 既存のテーブルを作成
        existing_payload = {
            'tableName': 'existing_table',
            'tableNumberOfRows': 10,
            'columnSettings': [{
                'columnName': 'test_col',
                'dataType': 'fixed',
                'fixedValue': 1
            }]
        }
        self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(existing_payload),
            content_type='application/json'
        )

        # 同じ名前のテーブルを再度作成しようとする
        duplicate_payload = {
            'tableName': 'existing_table',
            'tableNumberOfRows': 10,
            'columnSettings': [{
                'columnName': 'test_col2',
                'dataType': 'fixed',
                'fixedValue': 2
            }]
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(duplicate_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

    def test_validation_error_invalid_num_rows(self):
        """無効な行数のバリデーションエラーテスト"""

        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 0,  # 無効な行数
            'columnSettings': [{
                'columnName': 'test_col',
                'dataType': 'fixed',
                'fixedValue': 1
            }]
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

    def test_validation_error_empty_column_settings(self):
        """空の列設定のバリデーションエラーテスト"""

        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 10,
            'columnSettings': []  # 空の列設定
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

    def test_validation_error_missing_column_name(self):
        """列名が不足している場合のバリデーションエラーテスト"""

        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 10,
            'columnSettings': [{
                'dataType': 'fixed',
                'fixedValue': 1
                # 'columnName' が不足
            }]
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

    def test_validation_error_invalid_data_type(self):
        """無効なデータタイプのバリデーションエラーテスト"""

        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 10,
            'columnSettings': [{
                'columnName': 'test_col',
                'dataType': 'invalid_type',  # 無効なデータタイプ
                'fixedValue': 1
            }]
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

    def test_validation_error_missing_distribution_params(self):
        """分布パラメータが不足している場合のバリデーションエラーテスト"""

        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 10,
            'columnSettings': [{
                'columnName': 'test_col',
                'dataType': 'distribution',
                'distributionType': 'normal'
                # 'distributionParams' が不足
            }]
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

    def test_validation_error_missing_fixed_value(self):
        """固定値が不足している場合のバリデーションエラーテスト"""

        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 10,
            'columnSettings': [{
                'columnName': 'test_col',
                'dataType': 'fixed'
                # 'fixedValue' が不足
            }]
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

    def test_validation_error_invalid_distribution_type(self):
        """無効な分布タイプのバリデーションエラーテスト"""

        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 10,
            'columnSettings': [{
                'columnName': 'test_col',
                'dataType': 'distribution',
                'distributionType': 'invalid_distribution',  # 無効な分布タイプ
                'distributionParams': {'param1': 1}
            }]
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

    def test_validation_error_invalid_distribution_params(self):
        """無効な分布パラメータのバリデーションエラーテスト"""

        payload = {
            'tableName': 'test_table',
            'tableNumberOfRows': 10,
            'columnSettings': [{
                'columnName': 'test_col',
                'dataType': 'distribution',
                'distributionType': 'normal',
                'distributionParams': {'invalidParam': 1}  # 無効なパラメータ
            }]
        }

        response = self.client.post(
            '/api/create-simulation-data-table',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST

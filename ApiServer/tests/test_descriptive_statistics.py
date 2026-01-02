import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl

from main import app
from analysisapp.api.services.data.tables_manager import TablesManager


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
        # テーブルをクリア
        manager.clear_tables()
        # テスト用テーブルをセット (数値データ)
        df_numeric = pl.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10, 20, 30, 40, 50],
            'C': [5.234, 8.321, 2.976, 4.567, 9.629]
        })
        manager.store_table('TestTableNumeric', df_numeric)
        # テスト用テーブルをセット (文字列データ)
        df_string = pl.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie', 'Alice', 'Bob'],
            'category': ['A', 'B', 'A', 'A', 'C']
        })
        manager.store_table('TestTableString', df_string)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_descriptive_statistics_success_numeric(client, tables_manager):
    # 数値データに対する記述統計の計算が正常に動作する
    payload = {
        'tableName': 'TestTableNumeric',
        'columnNameList': ['A'],
        'statistics': ['mean', 'median', 'variance', 'std']
    }
    response = client.post(
        '/api/descriptive-statistics',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 結果の検証
    result = response_data['result']
    assert result['tableName'] == 'TestTableNumeric'
    self.assertAlmostEqual(result['statistics']['A']['mean'],
                           3.0, places=5)
    self.assertAlmostEqual(result['statistics']['A']['median'],
                           3.0, places=5)
    self.assertAlmostEqual(result['statistics']['A']['variance'],
                           2.5, places=5)
    self.assertAlmostEqual(result['statistics']['A']['std'],
                           1.5811388300841898, places=5)


def test_descriptive_statistics_success_all_stats(client, tables_manager):
    # 全ての統計を計算する
    payload = {
        'tableName': 'TestTableNumeric',
        'columnNameList': ['A', 'B', 'C'],
        'statistics': ['mean', 'mode', 'median',
                       'variance', 'std', 'range', 'iqr']
    }
    response = client.post(
        '/api/descriptive-statistics',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['tableName'] == 'TestTableNumeric'
    self.assertAlmostEqual(result['statistics']['B']['mean'],
                           30.0, places=5)
    self.assertAlmostEqual(result['statistics']['B']['median'],
                           30.0, places=5)
    self.assertAlmostEqual(result['statistics']['B']['range'],
                           40.0, places=5)
    self.assertAlmostEqual(result['statistics']['B']['iqr'],
                           20.0, places=5)


def test_descriptive_statistics_success_string_mode(client, tables_manager):
    # 文字列データに対するmode計算
    payload = {
        'tableName': 'TestTableString',
        'columnNameList': ['name'],
        'statistics': ['mode']
    }
    response = client.post(
        '/api/descriptive-statistics',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    # name列は ['Alice', 'Bob', 'Charlie', 'Alice', 'Bob'] なので、AliceかBobがmode
    assert result['statistics']['name']['mode'], ['Alice', 'Bob'])


def test_descriptive_statistics_string_numeric_stats(client, tables_manager):
    # 文字列データに対して数値専用統計を要求した場合はNoneが返される
    payload = {
        'tableName': 'TestTableString',
        'columnNameList': ['name'],
        'statistics': ['mean', 'variance', 'std', 'range', 'iqr']
    }
    response = client.post(
        '/api/descriptive-statistics',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    # 文字列列に対する数値統計はNone
    self.assertIsNone(result['statistics']['name']['mean'])
    self.assertIsNone(result['statistics']['name']['variance'])
    self.assertIsNone(result['statistics']['name']['std'])
    self.assertIsNone(result['statistics']['name']['range'])
    self.assertIsNone(result['statistics']['name']['iqr'])


def test_descriptive_statistics_invalid_table(client, tables_manager):
    # 存在しないテーブル名
    payload = {
        'tableName': 'NoTable',
        'columnNameList': ['A'],
        'statistics': ['mean']
    }
    response = client.post(
        '/api/descriptive-statistics',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable' does not exist",
                  response_data['message'])


def test_descriptive_statistics_invalid_column(client, tables_manager):
    # 存在しないカラム名を指定
    payload = {
        'tableName': 'TestTableNumeric',
        'columnNameList': ['A', 'Z'],
        'statistics': ['mean']
    }
    response = client.post(
        '/api/descriptive-statistics',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName 'Z' does not exist.",
                  response_data['message'])


def test_descriptive_statistics_invalid_statistic(client, tables_manager):
    # サポートされていない統計を指定
    payload = {
        'tableName': 'TestTableNumeric',
        'columnNameList': ['A'],
        'statistics': ['invalid_stat']
    }
    response = client.post(
        '/api/descriptive-statistics',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "statistics 'invalid_stat' is not supported",
                  response_data['message'])


def test_descriptive_statistics_empty_statistics_list(client, tables_manager):
    # 空の統計リストを指定
    payload = {
        'tableName': 'TestTableNumeric',
        'columnNameList': ['A'],
        'statistics': []
    }
    response = client.post(
        '/api/descriptive-statistics',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "statistics is required", response_data['message'])

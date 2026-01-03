import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl
import numpy as np

from main import app
from analysisapp.services.data.tables_manager import TablesManager


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
    manager.store_table('ConfidenceTestTable', df)
    # 数値以外のデータを含むテーブル（エラーテスト用）
    df_with_text = pl.DataFrame({
        'numeric_col': [1.0, 2.0, 3.0, 4.0],
        'text_col': ['a', 'b', 'c', 'd']
    })
    manager.store_table('TextTable', df_with_text)
    # 空データテーブル
    df_empty = pl.DataFrame({
        'empty_col': [None, None, None]
    })
    manager.store_table('EmptyTable', df_empty)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_confidence_interval_mean_success(client, tables_manager):
    """平均値の信頼区間計算が正常に動作する"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',
        'confidenceLevel': 0.95,
        'statisticType': 'mean'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 結果の構造をチェック
    result = response_data['result']
    assert 'tableName' in result
    assert 'columnName' in result
    assert 'statistic' in result
    assert 'confidence_interval' in result
    assert 'confidence_level' in result
    # 統計量の構造をチェック
    statistic = result['statistic']
    assert statistic['type'] == 'mean'
    assert isinstance(statistic['value'], (int, float))
    # 信頼区間の構造をチェック
    ci = result['confidence_interval']
    assert 'lower' in ci
    assert 'upper' in ci
    assert isinstance(ci['lower'], (int, float))
    assert isinstance(ci['upper'], (int, float))
    assert ci['lower'] < ci['upper']
    # 信頼度レベルのチェック
    assert result['confidence_level'] == 0.95
    assert result['columnName'] == 'normal_col'


def test_confidence_interval_median_success(client, tables_manager):
    """中央値の信頼区間計算が正常に動作する"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',
        'confidenceLevel': 0.90,
        'statisticType': 'median'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['statistic']['type'] == 'median'
    assert result['confidence_level'] == 0.90


def test_confidence_interval_proportion_success(client, tables_manager):
    """比率の信頼区間計算が正常に動作する"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'binary_col',
        'confidenceLevel': 0.95,
        'statisticType': 'proportion'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['statistic']['type'] == 'proportion'
    # 比率は0から1の間でなければならない
    proportion_value = result['statistic']['value']
    assert proportion_value >= 0
    assert proportion_value <= 1
    # 信頼区間も0から1の間
    ci = result['confidence_interval']
    assert ci['lower'] >= 0
    assert ci['upper'] <= 1


def test_confidence_interval_variance_success(client, tables_manager):
    """分散の信頼区間計算が正常に動作する"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',
        'confidenceLevel': 0.95,
        'statisticType': 'variance'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['statistic']['type'] == 'variance'
    # 分散は正の値でなければならない
    variance_value = result['statistic']['value']
    assert variance_value > 0


def test_confidence_interval_std_success(client, tables_manager):
    """標準偏差の信頼区間計算が正常に動作する"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',
        'confidenceLevel': 0.95,
        'statisticType': 'std'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['statistic']['type'] == 'std'
    # 標準偏差は正の値でなければならない
    std_value = result['statistic']['value']
    assert std_value > 0


def test_confidence_interval_invalid_table(client, tables_manager):
    """存在しないテーブル名でエラーが返される"""
    payload = {
        'tableName': 'NonExistentTable',
        'columnName': 'normal_col',
        'confidenceLevel': 0.95,
        'statisticType': 'mean'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NonExistentTable' does not exist" in response_data['message']


def test_confidence_interval_invalid_column(client, tables_manager):
    """存在しない列名でエラーが返される"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'nonexistent_column',
        'confidenceLevel': 0.95,
        'statisticType': 'mean'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName 'nonexistent_column' does not exist" in response_data['message']


def test_confidence_interval_invalid_statistic_type(client, tables_manager):
    """サポートされていない統計タイプでエラーが返される"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',
        'confidenceLevel': 0.95,
        'statisticType': 'invalid_stat'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "statisticType 'invalid_stat' is not supported" in response_data['message']


def test_confidence_interval_invalid_confidence_level_high(client, tables_manager):
    """信頼度レベルが1以上の場合エラーが返される"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',
        'confidenceLevel': 1.5,
        'statisticType': 'mean'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "confidenceLevel must be between 0 and 1" in response_data['message']


def test_confidence_interval_invalid_confidence_level_low(client, tables_manager):
    """信頼度レベルが0以下の場合エラーが返される"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',
        'confidenceLevel': 0,
        'statisticType': 'mean'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "confidenceLevel must be between 0 and 1" in response_data['message']


def test_confidence_interval_proportion_invalid_data(client, tables_manager):
    """比率計算で0,1以外のデータがある場合エラーが返される"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',  # 0,1以外の値を含む列
        'confidenceLevel': 0.95,
        'statisticType': 'proportion'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "data must contain only 0 and 1 values" in response_data['message']


def test_confidence_interval_empty_data(client, tables_manager):
    """空データの場合エラーが返される"""
    payload = {
        'tableName': 'EmptyTable',
        'columnName': 'empty_col',
        'confidenceLevel': 0.95,
        'statisticType': 'mean'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Column contains no valid data" in response_data['message']


def test_confidence_interval_missing_parameters(client, tables_manager):
    """必須パラメータが不足している場合エラーが返される"""
    # tableName がない場合
    payload = {
        'columnName': 'normal_col',
        'confidenceLevel': 0.95,
        'statisticType': 'mean'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response_data['detail'] is not None


def test_confidence_interval_different_levels(client, tables_manager):
    """異なる信頼度レベルでの計算が正常に動作する"""
    # 初期化しておく
    width_90 = width_95 = width_99 = None
    levels = [0.90, 0.95, 0.99]
    for level in levels:
        payload = {
            'tableName': 'ConfidenceTestTable',
            'columnName': 'normal_col',
            'confidenceLevel': level,
            'statisticType': 'mean'
        }
        response = client.post(
            '/api/confidence-interval',
            json=payload,
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data['code'] == 'OK'
        result = response_data['result']
        assert result['confidence_level'] == level
        # より高い信頼度レベルはより広い区間になるはず
        if level == 0.99:
            ci_99 = result['confidence_interval']
            width_99 = ci_99['upper'] - ci_99['lower']
        elif level == 0.95:
            ci_95 = result['confidence_interval']
            width_95 = ci_95['upper'] - ci_95['lower']
        elif level == 0.90:
            ci_90 = result['confidence_interval']
            width_90 = ci_90['upper'] - ci_90['lower']
    # 信頼区間の幅が信頼度レベルと正しい関係にあることを確認
    # 全ての変数が正しく計算されたかチェックしてから比較
    assert all([width_90, width_95, width_99])
    if width_90 and width_95 and width_99:
        assert width_90 < width_95 < width_99


def test_confidence_interval_json_structure_validation(client, tables_manager):
    """レスポンスのJSON構造が仕様通りである"""
    payload = {
        'tableName': 'ConfidenceTestTable',
        'columnName': 'normal_col',
        'confidenceLevel': 0.95,
        'statisticType': 'std'
    }
    response = client.post(
        '/api/confidence-interval',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    result = response_data['result']
    # 必須フィールドの存在確認
    required_fields = ['tableName', 'columnName', 'statistic',
                      'confidence_interval', 'confidence_level']
    for field in required_fields:
        assert field in result
    # statisticの必須フィールド
    statistic = result['statistic']
    assert 'type' in statistic
    assert 'value' in statistic
    # confidence_intervalの必須フィールド
    ci = result['confidence_interval']
    assert 'lower' in ci
    assert 'upper' in ci

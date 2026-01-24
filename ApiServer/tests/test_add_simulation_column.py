import polars as pl
import pytest
from analysisapp.services.data.tables_store import TablesStore
from fastapi import status
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50]
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_add_uniform_column_success(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'TestTable'
    assert response_data['result']['columnName'] == 'UniformCol'
    assert response_data['result']['distributionType'] == 'uniform'
    # データが追加されているか確認
    df = tables_store.get_table('TestTable').table
    assert 'UniformCol' in df.columns
    uniform_values = df['UniformCol'].to_list()
    assert len(uniform_values) == 5
    # 一様分布の範囲内にあることを確認
    assert all(0.0 <= val <= 1.0 for val in uniform_values)


def test_add_normal_column_success(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # データが追加されているか確認
    df = tables_store.get_table('TestTable').table
    assert 'NormalCol' in df.columns
    normal_values = df['NormalCol'].to_list()
    assert len(normal_values) == 5


def test_add_binomial_column_success(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # データが追加されているか確認
    df = tables_store.get_table('TestTable').table
    assert 'BinomialCol' in df.columns
    binomial_values = df['BinomialCol'].to_list()
    assert len(binomial_values) == 5
    # 二項分布の範囲内にあることを確認
    assert all(0 <= val <= 10 for val in binomial_values)


def test_add_exponential_column_success(client, tables_store):
    """指数分布の列追加が正常に動作することをテスト"""
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'ExponentialCol',
        'distributionType': 'exponential',
        'distributionParams': {
            'scale': 1.0
        }
    }
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # データが追加されているか確認
    df = tables_store.get_table('TestTable').table
    assert 'ExponentialCol' in df.columns
    exp_values = df['ExponentialCol'].to_list()
    assert len(exp_values) == 5
    # 指数分布は非負の値
    assert all(val >= 0 for val in exp_values)


def test_add_gamma_column_success(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK


def test_add_beta_column_success(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    # ベータ分布は[0,1]の範囲
    df = tables_store.get_table('TestTable').table
    beta_values = df['BetaCol'].to_list()
    assert all(0 <= val <= 1 for val in beta_values)


def test_add_poisson_column_success(client, tables_store):
    """ポアソン分布の列追加が正常に動作することをテスト"""
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'PoissonCol',
        'distributionType': 'poisson',
        'distributionParams': {
            'lam': 3.0
        }
    }
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    # ポアソン分布は非負の整数
    df = tables_store.get_table('TestTable').table
    poisson_values = df['PoissonCol'].to_list()
    assert all(val >= 0 for val in poisson_values)


def test_invalid_table_name(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable'は存在しません" in response_data['message']


def test_duplicate_column_name(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "newColumnName 'A'は既に存在します。" == response_data['message']


def test_unsupported_distribution(client, tables_store):
    """サポートされていない分布を指定した場合のテスト"""
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'TestCol',
        'distributionType': 'unsupported',
        'distributionParams': {}
    }
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = ("distributionType 'unsupported'はサポートされていません。"
               "サポートされるdistributionType: uniform, exponential, normal, "
               "gamma, beta, weibull, lognormal, binomial, bernoulli, "
               "poisson, geometric, hypergeometric")
    assert message == response_data['message']


def test_invalid_uniform_params(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "'low'は'high'より小さい必要があります" in response_data['message']


def test_missing_required_params(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "正規分布には'loc'と'scale'パラメータが必要です"
    assert message == response_data['message']


def test_invalid_param_type(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "locは数値である必要があります。" in response_data['message']


def test_negative_scale_normal(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "正規分布では、'scale'は正の値である必要があります" in response_data['message']


def test_binomial_invalid_p(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "'p'は0から1の間である必要があります" in response_data['message']


def test_hypergeometric_success(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'


def test_hypergeometric_invalid_params(client, tables_store):
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
    response = client.post(
        '/api/column/add-simulation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "'K'は'N'を超えてはいけません" in response_data['message']

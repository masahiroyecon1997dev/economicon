import numpy as np
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
    # プロビット分析用テストデータを作成
    # 二値の被説明変数（0または1）と複数の説明変数を持つテーブル
    np.random.seed(42)  # 再現可能な結果のため
    n_samples = 100
    # 説明変数の生成
    x1 = np.random.normal(0, 1, n_samples)
    x2 = np.random.normal(0, 1, n_samples)
    x3 = np.random.uniform(0, 10, n_samples)
    # プロビット関数を使用して被説明変数を生成
    # プロビット関数は標準正規分布の累積分布関数（CDF）を使用
    from scipy.stats import norm
    linear_combination = -1 + 0.5 * x1 + 1.2 * x2 + 0.1 * x3
    probabilities = norm.cdf(linear_combination)
    y = np.random.binomial(1, probabilities, n_samples)
    df = pl.DataFrame({
        'y': y,
        'x1': x1,
        'x2': x2,
        'x3': x3,
        'id': range(n_samples)
    })
    manager.store_table('ProbitTestTable', df)
    # 数値以外のデータを含むテーブル（エラーテスト用）
    df_with_text = pl.DataFrame({
        'y': [0, 1, 0, 1],
        'x1': [1.0, 2.0, 3.0, 4.0],
        'text_col': ['a', 'b', 'c', 'd']
    })
    manager.store_table('TextTable', df_with_text)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_probit_regression_success(client, tables_store):
    """正常にプロビット分析が実行できる"""
    payload = {
        'tableName': 'ProbitTestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 結果の構造をチェック
    result = response_data['result']
    assert 'tableName' in result
    assert 'dependentVariable' in result
    assert 'explanatoryVariables' in result
    assert 'regressionResult' in result
    assert 'parameters' in result
    assert 'modelStatistics' in result
    # パラメータの構造をチェック
    parameters = result['parameters']
    assert isinstance(parameters, list)
    assert len(parameters) == 3
    # 各パラメータに必要な情報があることを確認
    for param in parameters:
        assert 'variable' in param
        assert 'coefficient' in param
        assert 'pValue' in param
        assert 'tValue' in param
    # モデル統計情報をチェック
    stats = result['modelStatistics']
    assert 'AIC' in stats
    assert 'BIC' in stats
    assert 'logLikelihood' in stats
    assert 'pseudoRSquared' in stats
    assert 'nObservations' in stats


def test_probit_regression_multiple_variables(client, tables_store):
    """複数の説明変数でプロビット分析が実行できる"""
    payload = {
        'tableName': 'ProbitTestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2', 'x3']
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # パラメータ数をチェック（定数項 + 3つの説明変数）
    result = response_data['result']
    parameters = result['parameters']
    assert len(parameters) == 4


def test_probit_regression_invalid_table(client, tables_store):
    """存在しないテーブル名でエラーが返される"""
    payload = {
        'tableName': 'NonExistentTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "tableName 'NonExistentTable'は存在しません。"
    assert message == response_data['message']


def test_probit_regression_invalid_dependent_variable(client, tables_store):
    """存在しない被説明変数でエラーが返される"""
    payload = {
        'tableName': 'ProbitTestTable',
        'dependentVariable': 'nonexistent_y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "dependentVariable 'nonexistent_y'は存在しません。"
    assert message == response_data['message']


def test_probit_regression_invalid_explanatory_variable(client,
                                                        tables_store):
    """存在しない説明変数でエラーが返される"""
    payload = {
        'tableName': 'ProbitTestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'nonexistent_x']
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "explanatoryVariables 'nonexistent_x'は存在しません。"
    assert message == response_data['message']


def test_probit_regression_empty_explanatory_variables(client, tables_store):
    """説明変数が空の場合エラーが返される"""
    payload = {
        'tableName': 'ProbitTestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': []
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = ("explanatoryVariablesは少なくとも 1 つの "
               "explanatory_variableが必要です。")
    assert message == response_data['message']


def test_probit_regression_dependent_in_explanatory(client, tables_store):
    """被説明変数が説明変数に含まれている場合エラーが返される"""
    payload = {
        'tableName': 'ProbitTestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'y', 'x2']
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "被説明変数を説明変数に含めることはできません"
    assert message == response_data['message']


def test_probit_regression_missing_parameters(client, tables_store):
    """必須パラメータが不足している場合エラーが返される"""
    # tableName がない場合
    payload = {
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert response_data['code'] == 'NG'
    # assert "Required parameter is missing" == response_data['message']


def test_probit_regression_single_explanatory_variable(client, tables_store):
    """単一の説明変数でもプロビット分析が実行できる"""
    payload = {
        'tableName': 'ProbitTestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1']
    }
    response = client.post(
        '/api/regression/probit',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # パラメータ数をチェック（定数項 + 1つの説明変数）
    result = response_data['result']
    parameters = result['parameters']
    assert len(parameters) == 2

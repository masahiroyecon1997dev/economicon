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
    # 変量効果推定分析用テストデータを作成
    np.random.seed(42)  # 再現可能な結果のため
    n_samples = 100
    # 説明変数の生成
    x1 = np.random.normal(0, 1, n_samples)
    x2 = np.random.normal(0, 1, n_samples)
    x3 = np.random.uniform(0, 10, n_samples)
    # 被説明変数の生成（線形関係）
    y = 2.0 + 1.5 * x1 + 0.8 * x2 + 0.2 * x3 + np.random.normal(0, 0.5,
                                                                n_samples)
    df = pl.DataFrame({
        'y': y,
        'x1': x1,
        'x2': x2,
        'x3': x3,
        'id': range(n_samples)
    })
    manager.store_table('VEETestTable', df)
    # 数値以外のデータを含むテーブル（エラーテスト用）
    df_with_text = pl.DataFrame({
        'y': [1.0, 2.0, 3.0, 4.0],
        'x1': [1.0, 2.0, 3.0, 4.0],
        'text_col': ['a', 'b', 'c', 'd']
    })
    manager.store_table('TextTable', df_with_text)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_variable_effects_estimation_success_default(client, tables_store):
    """デフォルト設定で正常に変量効果推定分析が実行できる"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    print(response_data)
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 結果の構造をチェック
    result = response_data['result']
    assert 'tableName' in result
    assert 'dependentVariable' in result
    assert 'explanatoryVariables' in result
    assert 'standardErrorMethod' in result
    assert 'useTDistribution' in result
    assert 'regressionResult' in result
    assert 'parameters' in result
    assert 'modelStatistics' in result
    # デフォルト値をチェック
    assert result['standardErrorMethod'] == 'nonrobust'
    assert result['useTDistribution']
    # パラメータの構造をチェック
    parameters = result['parameters']
    assert isinstance(parameters, list)
    assert len(parameters) == 3
    # 各パラメータに必要な情報があることを確認
    for param in parameters:
        assert 'variable' in param
        assert 'coefficient' in param
        assert 'standardError' in param
        assert 'pValue' in param
        assert 'tValue' in param
        assert 'confidenceIntervalLower' in param
        assert 'confidenceIntervalUpper' in param
    # モデル統計情報をチェック
    stats = result['modelStatistics']
    expected_stats = ['R2', 'adjustedR2', 'AIC', 'BIC', 'fValue',
                      'fProbability', 'logLikelihood', 'nObservations',
                      'degreesOfFreedom', 'residualDegreesOfFreedom']
    for stat in expected_stats:
        assert stat in stats


def test_variable_effects_estimation_hc1_robust(client, tables_store):
    """HC1標準誤差で変量効果推定分析が実行できる"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2', 'x3'],
        'standardErrorMethod': 'HC1',
        'useTDistribution': False
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['standardErrorMethod'] == 'HC1'
    assert not result['useTDistribution']
    # パラメータ数をチェック（定数項 + 3つの説明変数）
    parameters = result['parameters']
    assert len(parameters) == 4


def test_variable_effects_estimation_hac(client, tables_store):
    """HAC標準誤差で変量効果推定分析が実行できる"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'standardErrorMethod': 'HAC',
        'useTDistribution': True
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['standardErrorMethod'] == 'HAC'
    assert result['useTDistribution']


def test_variable_effects_estimation_invalid_table(client, tables_store):
    """存在しないテーブル名でエラーが返される"""
    payload = {
        'tableName': 'NonExistentTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NonExistentTable' does not exist." \
        == response_data['message']


def test_variable_effects_estimation_invalid_dependent_variable(client,
                                                                tables_store
                                                                ):
    """存在しない被説明変数でエラーが返される"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'nonexistent_y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "dependentVariable 'nonexistent_y' does not exist." \
        == response_data['message']


def test_variable_effects_estimation_invalid_explanatory_variable(
        client, tables_store):
    """存在しない説明変数でエラーが返される"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'nonexistent_x']
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "explanatoryVariables 'nonexistent_x' does not exist." \
        == response_data['message']


def test_variable_effects_estimation_empty_explanatory_variables(
        client, tables_store):
    """説明変数が空の場合エラーが返される"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': []
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert ("explanatoryVariables must be with "
            "at least 1 explanatory_variable.") \
        == response_data['message']


def test_variable_effects_estimation_dependent_in_explanatory(
        client, tables_store):
    """被説明変数が説明変数に含まれている場合エラーが返される"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'y', 'x2']
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Dependent variable cannot be included in explanatory variables" \
        == response_data['message']


def test_variable_effects_estimation_invalid_standard_error_method(
        client, tables_store):
    """不正な標準誤差計算方法でエラーが返される"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'standardErrorMethod': 'invalid_method'
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert ("standardErrorMethod must be one of: ""nonrobust, HC0, HC1, "
            "HC2, HC3, HAC, hac-panel, hac-groupsum, cluster") \
        == response_data['message']


def test_variable_effects_estimation_missing_parameters(
        client, tables_store):
    """必須パラメータが不足している場合エラーが返される"""
    # tableName がない場合
    payload = {
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # response_data = response.json()
    # assert response_data['code'] == 'NG'
    # assert "Required parameter is missing." == response_data['message']


@pytest.mark.parametrize("method", ['nonrobust', 'HC0', 'HC1',
                                    'HC2', 'HC3', 'HAC'])
def test_variable_effects_estimation_all_standard_error_methods(client,
                                                                tables_store,
                                                                method):
    """全ての標準誤差計算方法が正常に動作する"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'standardErrorMethod': method,
        'useTDistribution': True
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['standardErrorMethod'] == method


def test_variable_effects_estimation_single_explanatory_variable(
        client, tables_store):
    """単一の説明変数でも変量効果推定分析が実行できる"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'standardErrorMethod': 'HC2',
        'useTDistribution': False
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # パラメータ数をチェック（定数項 + 1つの説明変数）
    result = response_data['result']
    parameters = result['parameters']
    assert len(parameters) == 2


def test_variable_effects_estimation_confidence_intervals(
        client, tables_store):
    """信頼区間が正しく計算される"""
    payload = {
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'standardErrorMethod': 'HC1',
        'useTDistribution': True
    }
    response = client.post(
        '/api/regression/variable-effects',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    result = response_data['result']
    parameters = result['parameters']
    # 各パラメータの信頼区間をチェック
    for param in parameters:
        lower = param['confidenceIntervalLower']
        upper = param['confidenceIntervalUpper']
        coefficient = param['coefficient']
        # 信頼区間の論理的な順序をチェック
        assert lower <= upper
        # 係数は信頼区間内にある（通常95%信頼区間）
        assert lower <= coefficient
        assert coefficient <= upper

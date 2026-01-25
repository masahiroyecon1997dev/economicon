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
    # 変量効果推定分析用テストデータを作成（パネルデータ）
    np.random.seed(42)  # 再現可能な結果のため
    n_entities = 20  # 個体数
    n_periods = 5    # 時点数
    n_total = n_entities * n_periods

    # 個体ID
    entity_ids = np.repeat(range(1, n_entities + 1), n_periods)
    # 時点ID
    time_ids = np.tile(range(1, n_periods + 1), n_entities)

    # ランダム効果
    random_effects = np.random.normal(0, 1, n_entities)
    random_effects_expanded = np.repeat(random_effects, n_periods)

    # 説明変数の生成
    x1 = np.random.normal(0, 1, n_total)
    x2 = np.random.normal(0, 1, n_total)

    # 被説明変数の生成（ランダム効果を含む）
    error = np.random.normal(0, 0.5, n_total)
    y = 2.0 + 1.5 * x1 + 0.8 * x2 + random_effects_expanded + error

    df = pl.DataFrame({
        'entity_id': entity_ids,
        'time_id': time_ids,
        'y': y,
        'x1': x1,
        'x2': x2
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
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/analysis/regression',
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
    assert 'entityIdColumn' in result
    assert 'regressionResult' in result
    assert 'parameters' in result
    assert 'modelStatistics' in result
    # パラメータの構造をチェック
    parameters = result['parameters']
    assert isinstance(parameters, list)
    assert len(parameters) == 2
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
    assert 'nObservations' in stats
    assert 'R2Within' in stats
    assert 'R2Between' in stats
    assert 'R2Overall' in stats


def test_variable_effects_estimation_hc1_robust(client, tables_store):
    """HC1標準誤差で変量効果推定分析が実行できる"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'hc1',
        'useTDistribution': False
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    # パラメータ数をチェック（2つの説明変数）
    parameters = result['parameters']
    assert len(parameters) == 2


def test_variable_effects_estimation_hac(client, tables_store):
    """HAC標準誤差で変量効果推定分析が実行できる"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'hac',
        'useTDistribution': True
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert 'parameters' in result


def test_variable_effects_estimation_invalid_table(client, tables_store):
    """存在しないテーブル名でエラーが返される"""
    payload = {
        'type': 're',
        'tableName': 'NonExistentTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NonExistentTable'は存在しません。" \
        == response_data['message']


def test_variable_effects_estimation_invalid_dependent_variable(client,
                                                                tables_store
                                                                ):
    """存在しない被説明変数でエラーが返される"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'nonexistent_y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "dependentVariable 'nonexistent_y'は存在しません。" \
        == response_data['message']


def test_variable_effects_estimation_invalid_explanatory_variable(
        client, tables_store):
    """存在しない説明変数でエラーが返される"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'nonexistent_x'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "explanatoryVariables 'nonexistent_x'は存在しません。" \
        == response_data['message']


def test_variable_effects_estimation_empty_explanatory_variables(
        client, tables_store):
    """説明変数が空の場合エラーが返される"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': [],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert ("explanatoryVariablesは少なくとも 1 つの "
            "explanatory_variableが必要です。") \
        == response_data['message']


def test_variable_effects_estimation_dependent_in_explanatory(
        client, tables_store):
    """被説明変数が説明変数に含まれている場合エラーが返される"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'y', 'x2'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "被説明変数を説明変数に含めることはできません。" \
        == response_data['message']


def test_variable_effects_estimation_invalid_standard_error_method(
        client, tables_store):
    """不正な標準誤差計算方法でエラーが返される（Pydanticバリデーション）"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'invalid_method'
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    # Pydanticのバリデーションエラーで422が返される
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_variable_effects_estimation_missing_parameters(
        client, tables_store):
    """必須パラメータが不足している場合エラーが返される"""
    # tableName がない場合
    payload = {
        'type': 're',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("method", ['nonrobust', 'hc0', 'hc1',
                                    'hc2', 'hc3', 'hac'])
def test_variable_effects_estimation_all_standard_error_methods(client,
                                                                tables_store,
                                                                method):
    """全ての標準誤差計算方法が正常に動作する"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': method,
        'useTDistribution': True
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert 'parameters' in result


def test_variable_effects_estimation_single_explanatory_variable(
        client, tables_store):
    """単一の説明変数でも変量効果推定分析が実行できる"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'hc2',
        'useTDistribution': False
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # パラメータ数をチェック（1つの説明変数）
    result = response_data['result']
    parameters = result['parameters']
    assert len(parameters) == 1


def test_variable_effects_estimation_confidence_intervals(
        client, tables_store):
    """信頼区間が正しく計算される"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'hc1',
        'useTDistribution': True
    }
    response = client.post(
        '/api/analysis/regression',
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

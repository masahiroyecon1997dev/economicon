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
    manager.store_table('PanelData', df_panel)
    # 単一時点のデータ（エラーテスト用）
    df_single = pl.DataFrame({
        'entity_id': [1, 2, 3],
        'y': [1.0, 2.0, 3.0],
        'x1': [1.0, 2.0, 3.0]
    })
    manager.store_table('SinglePeriod', df_single)
    # 数値以外のデータを含むテーブル（エラーテスト用）
    df_with_text = pl.DataFrame({
        'entity_id': [1, 1, 2, 2],
        'y': [1.0, 2.0, 3.0, 4.0],
        'x1': [1.0, 2.0, 3.0, 4.0],
        'text_col': ['a', 'b', 'c', 'd']
    })
    manager.store_table('TextTable', df_with_text)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_fixed_effects_estimation_success(client, tables_manager):
    """正常に固定効果推定が実行できる"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'normal',
        'useTDistribution': True
    }
    response = client.post(
        '/api/fixed-effects-estimation',
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
    assert 'entityIdColumn' in result
    assert 'estimationMethod' in result
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
        assert 'pValue' in param
        assert 'tValue' in param
        assert 'standardError' in param
    # モデル統計情報をチェック
    stats = result['modelStatistics']
    assert 'R2' in stats
    assert 'adjustedR2' in stats
    assert 'nObservations' in stats
    assert 'nEntities' in stats
    assert 'standardErrorMethod' in stats
    assert 'useTDistribution' in stats
    # 推定結果の妥当性をチェック（真の係数に近いか）
    x1_coeff = next(
        p['coefficient'] for p in parameters if p['variable'] == 'x1')
    x2_coeff = next(
        p['coefficient'] for p in parameters if p['variable'] == 'x2')
    # 真の係数: x1=1.5, x2=-0.8 に対する許容範囲
    assert x1_coeff == pytest.approx(1.5, abs=0.5)
    assert x2_coeff == pytest.approx(-0.8, abs=0.5)


def test_fixed_effects_estimation_robust_standard_errors(client, tables_manager):
    """頑健な標準誤差で固定効果推定が実行できる"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'robust',
        'useTDistribution': False
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['modelStatistics']['standardErrorMethod'] == 'robust'
    assert result['modelStatistics']['useTDistribution'] == False


def test_fixed_effects_estimation_clustered_standard_errors(client, tables_manager):
    """クラスター標準誤差で固定効果推定が実行できる"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'clustered',
        'useTDistribution': True
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['modelStatistics']['standardErrorMethod'] == 'clustered'


def test_fixed_effects_estimation_hac_standard_errors(client, tables_manager):
    """HAC標準誤差で固定効果推定が実行できる"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'hac',
        'useTDistribution': True
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['modelStatistics']['standardErrorMethod'] == 'hac'


def test_fixed_effects_estimation_invalid_table(client, tables_manager):
    """存在しないテーブル名でエラーが返される"""
    payload = {
        'tableName': 'NonExistentTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NonExistentTable' does not exist" == response_data['message']



def test_fixed_effects_estimation_invalid_dependent_variable(client, tables_manager):
    """存在しない被説明変数でエラーが返される"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'nonexistent_y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "dependentVariable 'nonexistent_y' does not exist" == response_data['message']


def test_fixed_effects_estimation_invalid_explanatory_variable(client, tables_manager):
    """存在しない説明変数でエラーが返される"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'nonexistent_x'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "explanatoryVariables 'nonexistent_x' does not exist" == response_data['message']


def test_fixed_effects_estimation_invalid_entity_id_column(client, tables_manager):
    """存在しない個体ID列でエラーが返される"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'nonexistent_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "entityIdColumn 'nonexistent_id' does not exist" == response_data['message']


def test_fixed_effects_estimation_entity_id_same_as_dependent(client, tables_manager):
    """個体ID列が被説明変数と同じ場合エラーが返される"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'y'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Entity ID column cannot be the same as dependent variable" == response_data['message']


def test_fixed_effects_estimation_entity_id_in_explanatory(client, tables_manager):
    """個体ID列が説明変数に含まれている場合エラーが返される"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'entity_id'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Entity ID column cannot be included in explanatory variables" == response_data['message']


def test_fixed_effects_estimation_invalid_standard_error_method(client, tables_manager):
    """無効な標準誤差計算方法でエラーが返される"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'invalid_method'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "is not supported. Supported standardErrorMethod:" == response_data['message']


def test_fixed_effects_estimation_single_period_data(client, tables_manager):
    """単一時点のデータでエラーが返される"""
    payload = {
        'tableName': 'SinglePeriod',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    assert "No entities with multiple observations found" == response_data['message']

def test_fixed_effects_estimation_empty_explanatory_variables(client, tables_manager):
    """説明変数が空の場合エラーが返される"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': [],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "explanatoryVariables must be with at least 1 explanatory_variable." == response_data['message']


def test_fixed_effects_estimation_dependent_in_explanatory(client, tables_manager):
    """被説明変数が説明変数に含まれている場合エラーが返される"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'y'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Dependent variable cannot be included in explanatory variables" == response_data['message']


def test_fixed_effects_estimation_missing_required_parameters(client, tables_manager):
    """必須パラメータが不足している場合エラーが返される"""
    # entityIdColumn がない場合
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1']
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Required parameter is missing" == response_data['message']


def test_fixed_effects_estimation_single_explanatory_variable(client, tables_manager):
    """単一の説明変数でも固定効果推定が実行できる"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # パラメータ数をチェック（1つの説明変数のみ）
    result = response_data['result']
    parameters = result['parameters']
    assert len(parameters) == 1
    assert parameters[0]['variable'] == 'x1'


def test_fixed_effects_estimation_with_default_parameters(client, tables_manager):
    """デフォルトパラメータで固定効果推定が実行できる"""
    payload = {
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post(
        '/api/fixed-effects-estimation',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    stats = result['modelStatistics']
    # デフォルト値の確認
    assert stats['standardErrorMethod'] == 'normal'
    assert stats['useTDistribution'] == True

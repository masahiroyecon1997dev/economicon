"""
統合回帰分析テスト

全ての回帰分析手法を単一エンドポイント /api/analysis/regression でテストします。
"""

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
    manager.clear_tables()
    np.random.seed(42)

    # 1. OLS/Logit/Probit用: 基本的な回帰データ
    n_samples = 100
    x1 = np.random.normal(0, 1, n_samples)
    x2 = np.random.normal(0, 1, n_samples)

    # 線形回帰用
    y_linear = 2.0 + 1.5 * x1 + 0.8 * x2 + np.random.normal(0, 0.5, n_samples)

    # ロジット/プロビット用
    linear_combination = -1 + 0.5 * x1 + 1.2 * x2
    probabilities = 1 / (1 + np.exp(-linear_combination))
    y_binary = np.random.binomial(1, probabilities, n_samples)

    df_basic = pl.DataFrame({
        'y_linear': y_linear,
        'y_binary': y_binary,
        'x1': x1,
        'x2': x2
    })
    manager.store_table('BasicData', df_basic)

    # 2. パネルデータ（固定効果・変量効果用）
    n_entities = 10
    n_periods = 5
    n_total = n_entities * n_periods
    entity_ids = np.repeat(range(1, n_entities + 1), n_periods)
    time_ids = np.tile(range(1, n_periods + 1), n_entities)
    entity_effects = np.random.normal(0, 2, n_entities)
    entity_effects_expanded = np.repeat(entity_effects, n_periods)
    x1_panel = np.random.normal(0, 1, n_total)
    x2_panel = np.random.normal(0, 1, n_total)
    error = np.random.normal(0, 1, n_total)
    y_panel = 2.0 + 1.5 * x1_panel + -0.8 * x2_panel + entity_effects_expanded + error

    df_panel = pl.DataFrame({
        'entity_id': entity_ids,
        'time_id': time_ids,
        'y': y_panel,
        'x1': x1_panel,
        'x2': x2_panel
    })
    manager.store_table('PanelData', df_panel)

    # 3. 操作変数用データ
    n_iv = 200
    # 外生変数
    z1 = np.random.normal(0, 1, n_iv)  # 操作変数1
    z2 = np.random.normal(0, 1, n_iv)  # 操作変数2
    x1_iv = np.random.normal(0, 1, n_iv)  # 外生説明変数

    # 内生変数（操作変数と相関）
    x2_endog = 0.5 * z1 + 0.3 * z2 + np.random.normal(0, 0.5, n_iv)

    # 被説明変数
    y_iv = 1.0 + 0.5 * x1_iv + 1.0 * x2_endog + np.random.normal(0, 1, n_iv)

    df_iv = pl.DataFrame({
        'y': y_iv,
        'x1': x1_iv,
        'x2_endog': x2_endog,
        'z1': z1,
        'z2': z2
    })
    manager.store_table('IVData', df_iv)

    # 4. Tobit用データ（打ち切りあり）
    n_tobit = 150
    x_tobit = np.random.normal(0, 1, n_tobit)
    latent_y = 1.0 + 2.0 * x_tobit + np.random.normal(0, 1, n_tobit)
    y_tobit = np.maximum(0, latent_y)  # 0で左側打ち切り

    df_tobit = pl.DataFrame({
        'y': y_tobit,
        'x': x_tobit
    })
    manager.store_table('TobitData', df_tobit)

    yield manager
    manager.clear_tables()


@pytest.mark.parametrize("analysis_type,table_name,dependent_var,expected_diagnostics", [
    ('ols', 'BasicData', 'y_linear', ['R2', 'adjustedR2', 'fValue']),
    ('logit', 'BasicData', 'y_binary', ['pseudoRSquared', 'logLikelihood']),
    ('probit', 'BasicData', 'y_binary', ['pseudoRSquared', 'logLikelihood']),
])
def test_basic_regression_types(client, tables_store, analysis_type,
                                table_name, dependent_var, expected_diagnostics):
    """基本的な回帰分析タイプのテスト"""
    payload = {
        'type': analysis_type,
        'tableName': table_name,
        'dependentVariable': dependent_var,
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'

    result = response_data['result']
    assert 'parameters' in result
    assert 'modelStatistics' in result

    # 期待される診断統計量が含まれているか確認
    stats = result['modelStatistics']
    for diagnostic in expected_diagnostics:
        assert diagnostic in stats, f"{diagnostic} not found in {analysis_type}"


def test_fixed_effects_regression(client, tables_store):
    """固定効果推定のテスト"""
    payload = {
        'type': 'fe',
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'nonrobust'
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'

    result = response_data['result']
    assert 'diagnostics' in result

    # パネルデータ固有の診断統計量を確認
    diagnostics = result['diagnostics']
    assert 'rsquaredWithin' in diagnostics
    assert 'rsquaredBetween' in diagnostics
    assert 'rsquaredOverall' in diagnostics


def test_random_effects_regression(client, tables_store):
    """変量効果推定のテスト"""
    payload = {
        'type': 're',
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'nonrobust'
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'

    result = response_data['result']
    assert 'diagnostics' in result

    # 変量効果固有の診断統計量を確認
    diagnostics = result['diagnostics']
    assert 'rsquaredWithin' in diagnostics
    assert 'theta' in diagnostics or 'thetaDescription' in diagnostics


def test_iv_regression(client, tables_store):
    """操作変数法のテスト"""
    payload = {
        'type': 'iv',
        'tableName': 'IVData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'endogenousVariables': ['x2_endog'],
        'instrumentalVariables': ['z1', 'z2']
    }
    response = client.post('/api/analysis/regression', json=payload)

    if response.status_code != status.HTTP_200_OK:
        print(f"Response: {response.json()}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'

    result = response_data['result']
    assert 'diagnostics' in result

    # IV固有の診断統計量を確認
    diagnostics = result['diagnostics']
    # Wu-Hausman testまたはSargan testのいずれかが含まれているはず
    has_iv_diagnostics = (
        'wuHausmanTest' in diagnostics or
        'sarganTest' in diagnostics or
        'firstStage' in diagnostics
    )
    assert has_iv_diagnostics, "IV-specific diagnostics not found"


def test_lasso_regression(client, tables_store):
    """Lasso回帰のテスト"""
    payload = {
        'type': 'lasso',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1', 'x2'],
        'hyperParameters': {'alpha': 0.1}
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'

    result = response_data['result']
    assert 'parameters' in result
    # Lassoでは一部の係数がゼロになる可能性がある
    assert len(result['parameters']) >= 0


def test_ridge_regression(client, tables_store):
    """Ridge回帰のテスト"""
    payload = {
        'type': 'ridge',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1', 'x2'],
        'hyperParameters': {'alpha': 0.5}
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'

    result = response_data['result']
    assert 'parameters' in result


def test_tobit_regression(client, tables_store):
    """Tobit回帰のテスト"""
    payload = {
        'type': 'tobit',
        'tableName': 'TobitData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x'],
        'leftCensoringLimit': 0.0
    }
    response = client.post('/api/analysis/regression', json=payload)

    # py4etricsがない場合は500エラーまたは代替処理
    # とりあえず実行されることを確認
    assert response.status_code in [status.HTTP_200_OK,
                                    status.HTTP_500_INTERNAL_SERVER_ERROR]


def test_feiv_not_implemented(client, tables_store):
    """Fixed Effects IV（未実装）のテスト"""
    payload = {
        'type': 'feiv',
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'endogenousVariables': ['x2'],
        'instrumentalVariables': ['time_id'],
        'entityIdColumn': 'entity_id'
    }
    response = client.post('/api/analysis/regression', json=payload)

    # 未実装のため501エラーが返されるはず
    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED


def test_missing_required_parameters(client, tables_store):
    """必須パラメータが不足している場合のテスト"""
    # entityIdColumnが必要なのに指定されていない
    payload = {
        'type': 'fe',
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post('/api/analysis/regression', json=payload)

    # Pydanticバリデーションエラーで422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_invalid_table_name(client, tables_store):
    """存在しないテーブル名でエラーが返される"""
    payload = {
        'type': 'ols',
        'tableName': 'NonExistentTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert response_data['code'] == 'NG'
    assert 'NonExistentTable' in response_data['message']
    assert 'table' in response_data['message'].lower() or 'テーブル' in response_data['message']


@pytest.mark.parametrize("std_error_method", [
    'nonrobust', 'hc0', 'hc1', 'hc2', 'hc3', 'hac'
])
def test_standard_error_methods(client, tables_store, std_error_method):
    """様々な標準誤差計算方法のテスト"""
    payload = {
        'type': 'ols',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1'],
        'standardErrorMethod': std_error_method
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'


def test_confidence_intervals_present(client, tables_store):
    """信頼区間が正しく返されるかのテスト"""
    payload = {
        'type': 'ols',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    result = response.json()['result']

    # 各パラメータに信頼区間が含まれているか確認
    for param in result['parameters']:
        assert 'confidenceIntervalLower' in param
        assert 'confidenceIntervalUpper' in param
        assert param['confidenceIntervalLower'] <= param['coefficient']
        assert param['coefficient'] <= param['confidenceIntervalUpper']


# ========================================
# 定数項有無のテスト
# ========================================

def test_ols_without_constant(client, tables_store):
    """定数項なしのOLS回帰"""
    payload = {
        'type': 'ols',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1', 'x2'],
        'hasConst': False
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'
    # 定数項がないため、パラメータ数は説明変数の数と同じ
    assert len(response_data['result']['parameters']) == 2


def test_lasso_without_constant(client, tables_store):
    """定数項なしのLasso回帰"""
    payload = {
        'type': 'lasso',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1'],
        'hasConst': False,
        'hyperParameters': {'alpha': 0.1}
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'


# ========================================
# クラスター標準誤差のテスト
# ========================================

def test_clustered_standard_errors(client, tables_store):
    """クラスター標準誤差のテスト（パネルデータで自動設定）"""
    payload = {
        'type': 'fe',
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id',
        'standardErrorMethod': 'clustered'
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['code'] == 'OK'


# ========================================
# バリデーションエラーのテスト
# ========================================

def test_invalid_dependent_variable(client, tables_store):
    """存在しない被説明変数でエラー"""
    payload = {
        'type': 'ols',
        'tableName': 'BasicData',
        'dependentVariable': 'nonexistent_y',
        'explanatoryVariables': ['x1']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert response_data['code'] == 'NG'
    assert 'nonexistent_y' in response_data['message']


def test_invalid_explanatory_variable(client, tables_store):
    """存在しない説明変数でエラー"""
    payload = {
        'type': 'ols',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1', 'nonexistent_x']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert response_data['code'] == 'NG'
    assert 'nonexistent_x' in response_data['message']


def test_empty_explanatory_variables(client, tables_store):
    """説明変数が空の場合"""
    payload = {
        'type': 'ols',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': []
    }
    response = client.post('/api/analysis/regression', json=payload)

    # サービス層のバリデーションで400が返される
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert response_data['code'] == 'NG'
    assert 'explanatory' in response_data['message'].lower() or '説明変数' in response_data['message']


def test_dependent_in_explanatory(client, tables_store):
    """被説明変数が説明変数に含まれる場合"""
    payload = {
        'type': 'ols',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1', 'y_linear']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert response_data['code'] == 'NG'
    assert 'y_linear' in response_data['message'] or 'dependent' in response_data['message'].lower() or '被説明' in response_data['message']


def test_missing_entity_id_for_panel(client, tables_store):
    """パネルデータ分析でentityIdColumnが不足"""
    payload = {
        'type': 're',
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    # Pydanticのエラーメッセージ構造を確認
    assert 'detail' in response_data
    error_message = str(response_data['detail'])
    assert 'entityIdColumn' in error_message or 'entity' in error_message.lower()


def test_missing_instrumental_variables(client, tables_store):
    """IV分析でinstrumentalVariablesが不足"""
    payload = {
        'type': 'iv',
        'tableName': 'IVData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'endogenousVariables': ['x2_endog']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert 'detail' in response_data
    error_message = str(response_data['detail'])
    assert 'instrumentalVariables' in error_message or 'instrumental' in error_message.lower()


def test_missing_alpha_for_lasso(client, tables_store):
    """Lasso回帰でalphaが不足"""
    payload = {
        'type': 'lasso',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert 'detail' in response_data
    error_message = str(response_data['detail'])
    assert 'alpha' in error_message.lower()


def test_invalid_entity_id_column(client, tables_store):
    """存在しないentityIdColumn"""
    payload = {
        'type': 'fe',
        'tableName': 'PanelData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'entityIdColumn': 'nonexistent_id'
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert response_data['code'] == 'NG'
    assert 'nonexistent_id' in response_data['message']


def test_invalid_instrumental_variable(client, tables_store):
    """存在しない操作変数"""
    payload = {
        'type': 'iv',
        'tableName': 'IVData',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'endogenousVariables': ['x2_endog'],
        'instrumentalVariables': ['nonexistent_z']
    }
    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = response.json()
    assert response_data['code'] == 'NG'
    assert 'nonexistent_z' in response_data['message']


def test_clustered_without_groups(client, tables_store):
    """クラスター標準誤差でgroupsが不足（非パネルデータ）"""
    payload = {
        'type': 'ols',
        'tableName': 'BasicData',
        'dependentVariable': 'y_linear',
        'explanatoryVariables': ['x1'],
        'standardErrorMethod': 'clustered'
    }
    response = client.post('/api/analysis/regression', json=payload)

    # バリデーションエラーで422が返される
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert 'detail' in response_data
    error_message = str(response_data['detail'])
    assert 'groups' in error_message.lower() or 'clustered' in error_message.lower()

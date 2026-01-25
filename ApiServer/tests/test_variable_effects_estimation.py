import numpy as np
import polars as pl
import pytest
from analysisapp.services.data.tables_store import TablesStore
from fastapi import status
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """TestClient縺ｮ繝輔ぅ繧ｯ繧ｹ繝√Ε"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStore縺ｮ繝輔ぅ繧ｯ繧ｹ繝√Ε"""
    manager = TablesStore()
    # 繝・・繝悶Ν繧偵け繝ｪ繧｢
    manager.clear_tables()
    # 螟蛾㍼蜉ｹ譫懈耳螳壼・譫千畑繝・せ繝医ョ繝ｼ繧ｿ繧剃ｽ懈・・医ヱ繝阪Ν繝・・繧ｿ・・
    np.random.seed(42)  # 蜀咲樟蜿ｯ閭ｽ縺ｪ邨先棡縺ｮ縺溘ａ
    n_entities = 20  # 蛟倶ｽ捺焚
    n_periods = 5    # 譎らせ謨ｰ
    n_total = n_entities * n_periods
    
    # 蛟倶ｽ的D
    entity_ids = np.repeat(range(1, n_entities + 1), n_periods)
    # 譎らせID
    time_ids = np.tile(range(1, n_periods + 1), n_entities)
    
    # 繝ｩ繝ｳ繝繝蜉ｹ譫・
    random_effects = np.random.normal(0, 1, n_entities)
    random_effects_expanded = np.repeat(random_effects, n_periods)
    
    # 隱ｬ譏主､画焚縺ｮ逕滓・
    x1 = np.random.normal(0, 1, n_total)
    x2 = np.random.normal(0, 1, n_total)
    
    # 陲ｫ隱ｬ譏主､画焚縺ｮ逕滓・・医Λ繝ｳ繝繝蜉ｹ譫懊ｒ蜷ｫ繧・・
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
    # 謨ｰ蛟､莉･螟悶・繝・・繧ｿ繧貞性繧繝・・繝悶Ν・医お繝ｩ繝ｼ繝・せ繝育畑・・
    df_with_text = pl.DataFrame({
        'y': [1.0, 2.0, 3.0, 4.0],
        'x1': [1.0, 2.0, 3.0, 4.0],
        'text_col': ['a', 'b', 'c', 'd']
    })
    manager.store_table('TextTable', df_with_text)
    yield manager
    # 繝・せ繝亥ｾ後・繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・
    manager.clear_tables()


def test_variable_effects_estimation_success_default(client, tables_store):
    """繝・ヵ繧ｩ繝ｫ繝郁ｨｭ螳壹〒豁｣蟶ｸ縺ｫ螟蛾㍼蜉ｹ譫懈耳螳壼・譫舌′螳溯｡後〒縺阪ｋ"""
    payload = {
        'type': 're',
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'entityIdColumn': 'entity_id',
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
    # 邨先棡縺ｮ讒矩繧偵メ繧ｧ繝・け
    result = response_data['result']
    assert 'tableName' in result
    assert 'dependentVariable' in result
    assert 'explanatoryVariables' in result
    assert 'entityIdColumn': 'entity_id',
        'entityIdColumn' in result
    assert 'regressionResult' in result
    assert 'parameters' in result
    assert 'modelStatistics' in result
    # 繝代Λ繝｡繝ｼ繧ｿ縺ｮ讒矩繧偵メ繧ｧ繝・け
    parameters = result['parameters']
    assert isinstance(parameters, list)
    assert len(parameters) == 2
    # 蜷・ヱ繝ｩ繝｡繝ｼ繧ｿ縺ｫ蠢・ｦ√↑諠・ｱ縺後≠繧九％縺ｨ繧堤｢ｺ隱・
    for param in parameters:
        assert 'variable' in param
        assert 'coefficient' in param
        assert 'standardError' in param
        assert 'pValue' in param
        assert 'tValue' in param
        assert 'confidenceIntervalLower' in param
        assert 'confidenceIntervalUpper' in param
    # 繝｢繝・Ν邨ｱ險域ュ蝣ｱ繧偵メ繧ｧ繝・け
    stats = result['modelStatistics']
    assert 'nObservations' in stats
    assert 'R2Within' in stats
    assert 'R2Between' in stats
    assert 'R2Overall' in stats


def test_variable_effects_estimation_hc1_robust(client, tables_store):
    """HC1讓呎ｺ冶ｪ､蟾ｮ縺ｧ螟蛾㍼蜉ｹ譫懈耳螳壼・譫舌′螳溯｡後〒縺阪ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2', 'x3'],
        'standardErrorMethod': 'HC1',
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
    assert result['standardErrorMethod'] == 'HC1'
    assert not result['useTDistribution']
    # 繝代Λ繝｡繝ｼ繧ｿ謨ｰ繧偵メ繧ｧ繝・け・亥ｮ壽焚鬆・+ 3縺､縺ｮ隱ｬ譏主､画焚・・
    parameters = result['parameters']
    assert len(parameters) == 4


def test_variable_effects_estimation_hac(client, tables_store):
    """HAC讓呎ｺ冶ｪ､蟾ｮ縺ｧ螟蛾㍼蜉ｹ譫懈耳螳壼・譫舌′螳溯｡後〒縺阪ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'standardErrorMethod': 'HAC',
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
    assert result['standardErrorMethod'] == 'HAC'
    assert result['useTDistribution']


def test_variable_effects_estimation_invalid_table(client, tables_store):
    """蟄伜惠縺励↑縺・ユ繝ｼ繝悶Ν蜷阪〒繧ｨ繝ｩ繝ｼ縺瑚ｿ斐＆繧後ｋ"""
    payload = {
        'type': 're',
        'tableName': 'NonExistentTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NonExistentTable'縺ｯ蟄伜惠縺励∪縺帙ｓ縲・ \
        == response_data['message']


def test_variable_effects_estimation_invalid_dependent_variable(client,
                                                                tables_store
                                                                ):
    """蟄伜惠縺励↑縺・｢ｫ隱ｬ譏主､画焚縺ｧ繧ｨ繝ｩ繝ｼ縺瑚ｿ斐＆繧後ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'nonexistent_y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "dependentVariable 'nonexistent_y'縺ｯ蟄伜惠縺励∪縺帙ｓ縲・ \
        == response_data['message']


def test_variable_effects_estimation_invalid_explanatory_variable(
        client, tables_store):
    """蟄伜惠縺励↑縺・ｪｬ譏主､画焚縺ｧ繧ｨ繝ｩ繝ｼ縺瑚ｿ斐＆繧後ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'nonexistent_x']
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "explanatoryVariables 'nonexistent_x'縺ｯ蟄伜惠縺励∪縺帙ｓ縲・ \
        == response_data['message']


def test_variable_effects_estimation_empty_explanatory_variables(
        client, tables_store):
    """隱ｬ譏主､画焚縺檎ｩｺ縺ｮ蝣ｴ蜷医お繝ｩ繝ｼ縺瑚ｿ斐＆繧後ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': []
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert ("explanatoryVariables縺ｯ蟆代↑縺上→繧・1 縺､縺ｮ "
            "explanatory_variable縺悟ｿ・ｦ√〒縺吶・) \
        == response_data['message']


def test_variable_effects_estimation_dependent_in_explanatory(
        client, tables_store):
    """陲ｫ隱ｬ譏主､画焚縺瑚ｪｬ譏主､画焚縺ｫ蜷ｫ縺ｾ繧後※縺・ｋ蝣ｴ蜷医お繝ｩ繝ｼ縺瑚ｿ斐＆繧後ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'y', 'x2']
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "陲ｫ隱ｬ譏主､画焚繧定ｪｬ譏主､画焚縺ｫ蜷ｫ繧√ｋ縺薙→縺ｯ縺ｧ縺阪∪縺帙ｓ縲・ \
        == response_data['message']


def test_variable_effects_estimation_invalid_standard_error_method(
        client, tables_store):
    """荳肴ｭ｣縺ｪ讓呎ｺ冶ｪ､蟾ｮ險育ｮ玲婿豕輔〒繧ｨ繝ｩ繝ｼ縺瑚ｿ斐＆繧後ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'standardErrorMethod': 'invalid_method'
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert ("standardErrorMethod縺ｯ谺｡縺ｮ縺・★繧後°縺ｧ縺ゅｋ蠢・ｦ√′縺ゅｊ縺ｾ縺・ nonrobust, HC0, HC1, "
            "HC2, HC3, HAC, hac-panel, hac-groupsum, cluster") \
        == response_data['message']


def test_variable_effects_estimation_missing_parameters(
        client, tables_store):
    """蠢・医ヱ繝ｩ繝｡繝ｼ繧ｿ縺御ｸ崎ｶｳ縺励※縺・ｋ蝣ｴ蜷医お繝ｩ繝ｼ縺瑚ｿ斐＆繧後ｋ"""
    # tableName 縺後↑縺・ｴ蜷・
    payload = {
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2']
    }
    response = client.post(
        '/api/analysis/regression',
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
    """蜈ｨ縺ｦ縺ｮ讓呎ｺ冶ｪ､蟾ｮ險育ｮ玲婿豕輔′豁｣蟶ｸ縺ｫ蜍穂ｽ懊☆繧・""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
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
    assert result['standardErrorMethod'] == method


def test_variable_effects_estimation_single_explanatory_variable(
        client, tables_store):
    """蜊倅ｸ縺ｮ隱ｬ譏主､画焚縺ｧ繧ょ､蛾㍼蜉ｹ譫懈耳螳壼・譫舌′螳溯｡後〒縺阪ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1'],
        'standardErrorMethod': 'HC2',
        'useTDistribution': False
    }
    response = client.post(
        '/api/analysis/regression',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 繝代Λ繝｡繝ｼ繧ｿ謨ｰ繧偵メ繧ｧ繝・け・亥ｮ壽焚鬆・+ 1縺､縺ｮ隱ｬ譏主､画焚・・
    result = response_data['result']
    parameters = result['parameters']
    assert len(parameters) == 2


def test_variable_effects_estimation_confidence_intervals(
        client, tables_store):
    """菫｡鬆ｼ蛹ｺ髢薙′豁｣縺励￥險育ｮ励＆繧後ｋ"""
    payload = {
        'type': 're',
        'tableName': 'VEETestTable',
        'dependentVariable': 'y',
        'explanatoryVariables': ['x1', 'x2'],
        'standardErrorMethod': 'HC1',
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
    # 蜷・ヱ繝ｩ繝｡繝ｼ繧ｿ縺ｮ菫｡鬆ｼ蛹ｺ髢薙ｒ繝√ぉ繝・け
    for param in parameters:
        lower = param['confidenceIntervalLower']
        upper = param['confidenceIntervalUpper']
        coefficient = param['coefficient']
        # 菫｡鬆ｼ蛹ｺ髢薙・隲也炊逧・↑鬆・ｺ上ｒ繝√ぉ繝・け
        assert lower <= upper
        # 菫よ焚縺ｯ菫｡鬆ｼ蛹ｺ髢灘・縺ｫ縺ゅｋ・磯壼ｸｸ95%菫｡鬆ｼ蛹ｺ髢難ｼ・
        assert lower <= coefficient
        assert coefficient <= upper

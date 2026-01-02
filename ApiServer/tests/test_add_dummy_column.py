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
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'gender': ['male', 'female', 'female', 'male', 'other'],
        'age': [25, 30, 35, 40, 28]
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_add_dummy_column_success(client, tables_manager):
    # 正常にダミー変数列を追加できる
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'gender',
        'dummyColumnName': 'is_female',
        'targetValue': 'female'
    }
    response = client.post(
        '/api/add-dummy-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'TestTable'
    assert response_data['result']['dummyColumnName'] == 'is_female'
    # ダミー変数列が正しく作成されているかチェック
    df = tables_manager.get_table('TestTable').table
    assert 'is_female' in df.columns
    # femaleの値が1、それ以外が0になっているかチェック
    expected_values = [0, 1, 1, 0, 0]  # male, female, female, male, other
    assert df['is_female'].to_list() == expected_values


def test_add_dummy_column_invalid_table(client, tables_manager):
    # 存在しないテーブル名
    payload = {
        'tableName': 'NoTable',
        'sourceColumnName': 'gender',
        'dummyColumnName': 'is_female',
        'targetValue': 'female'
    }
    response = client.post(
        '/api/add-dummy-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert 'NoTable' in response_data['message']
    assert 'does not exist' in response_data['message']


def test_add_dummy_column_invalid_source_column(client, tables_manager):
    # 存在しないソース列名を指定
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'invalid_column',
        'dummyColumnName': 'is_female',
        'targetValue': 'female'
    }
    response = client.post(
        '/api/add-dummy-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert 'invalid_column' in response_data['message']
    assert 'does not exist' in response_data['message']


def test_add_dummy_column_duplicate_column_name(client, tables_manager):
    # 既存の列名をダミー列名として指定
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'gender',
        'dummyColumnName': 'age',  # 既存の列名
        'targetValue': 'female'
    }
    response = client.post(
        '/api/add-dummy-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert 'age' in response_data['message']


def test_add_dummy_column_with_numeric_target(client, tables_manager):
    # 数値のターゲット値でダミー変数を作成
    # 新しいテーブルを作成
    df_numeric = pl.DataFrame({
        'score': [85, 90, 75, 90, 88],
        'name': ['A', 'B', 'C', 'D', 'E']
    })
    tables_manager.store_table('NumericTable', df_numeric)
    payload = {
        'tableName': 'NumericTable',
        'sourceColumnName': 'score',
        'dummyColumnName': 'is_excellent',
        'targetValue': '90'
    }
    response = client.post(
        '/api/add-dummy-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # ダミー変数列が正しく作成されているかチェック
    df = tables_manager.get_table('NumericTable').table
    expected_values = [0, 1, 0, 1, 0]  # 90の位置のみ1
    assert df['is_excellent'].to_list() == expected_values

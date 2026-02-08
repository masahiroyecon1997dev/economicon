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
        'gender': ['male', 'female', 'female', 'male', 'other'],
        'age': [25, 30, 35, 40, 28]
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_add_dummy_column_success(client, tables_store):
    # 正常にダミー変数列を追加できる
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'gender',
        'dummyColumnName': 'is_female',
        'targetValue': 'female'
    }
    response = client.post(
        '/api/column/add-dummy',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'TestTable'
    assert response_data['result']['dummyColumnName'] == 'is_female'
    # ダミー変数列が正しく作成されているかチェック
    df = tables_store.get_table('TestTable').table
    assert 'is_female' in df.columns
    # femaleの値が1、それ以外が0になっているかチェック
    expected_values = [0, 1, 1, 0, 0]  # male, female, female, male, other
    assert df['is_female'].to_list() == expected_values


def test_add_dummy_column_invalid_table(client, tables_store):
    # 存在しないテーブル名
    payload = {
        'tableName': 'NoTable',
        'sourceColumnName': 'gender',
        'dummyColumnName': 'is_female',
        'targetValue': 'female'
    }
    response = client.post(
        '/api/column/add-dummy',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable'は存在しません。" == response_data['message']


def test_add_dummy_column_invalid_source_column(client, tables_store):
    # 存在しないソース列名を指定
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'invalid_column',
        'dummyColumnName': 'is_female',
        'targetValue': 'female'
    }
    response = client.post(
        '/api/column/add-dummy',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "sourceColumnName 'invalid_column'は存在しません。" \
        == response_data['message']


def test_add_dummy_column_duplicate_column_name(client, tables_store):
    # 既存の列名をダミー列名として指定
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'gender',
        'dummyColumnName': 'age',  # 既存の列名
        'targetValue': 'female'
    }
    response = client.post(
        '/api/column/add-dummy',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "dummyColumnName 'age'は既に存在します。" == response_data['message']


def test_add_dummy_column_with_numeric_target(client, tables_store):
    # 数値のターゲット値でダミー変数を作成
    # 新しいテーブルを作成
    df_numeric = pl.DataFrame({
        'score': [85, 90, 75, 90, 88],
        'name': ['A', 'B', 'C', 'D', 'E']
    })
    tables_store.store_table('NumericTable', df_numeric)
    payload = {
        'tableName': 'NumericTable',
        'sourceColumnName': 'score',
        'dummyColumnName': 'is_excellent',
        'targetValue': '90'
    }
    response = client.post(
        '/api/column/add-dummy',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # ダミー変数列が正しく作成されているかチェック
    df = tables_store.get_table('NumericTable').table
    expected_values = [0, 1, 0, 1, 0]  # 90の位置のみ1
    assert df['is_excellent'].to_list() == expected_values

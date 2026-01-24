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
def prepared_data():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6],
        'C': ['x', 'y', 'z']
    })
    manager.store_table('TestTable', df)
    yield manager, df
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_duplicate_table_success(client, prepared_data):
    tables_store, df = prepared_data
    # 正常にテーブル複製できる
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'DuplicatedTable'
    }
    response = client.post(
        '/api/table/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'DuplicatedTable'
    # 複製されたテーブルが存在することを確認
    table_list = tables_store.get_table_name_list()
    assert 'DuplicatedTable' in table_list
    # 複製されたテーブルの内容が元のテーブルと同じことを確認
    original_df = tables_store.get_table('TestTable').table
    duplicated_df = tables_store.get_table('DuplicatedTable').table
    # データフレームの内容が同じかチェック
    assert original_df.equals(duplicated_df)
    # 列名が同じかチェック
    assert original_df.columns == duplicated_df.columns
    # データが同じかチェック
    assert original_df['A'].to_list() == duplicated_df['A'].to_list()
    assert original_df['B'].to_list() == duplicated_df['B'].to_list()
    assert original_df['C'].to_list() == duplicated_df['C'].to_list()


def test_duplicate_table_invalid_source_table(client, prepared_data):
    tables_store, df = prepared_data
    # 存在しないソーステーブル名
    payload = {
        'tableName': 'NonExistentTable',
        'newTableName': 'DuplicatedTable'
    }
    response = client.post(
        '/api/table/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "tableName 'NonExistentTable'は存在しません。"
    assert message == response_data['message']


def test_duplicate_table_existing_destination_table(client, prepared_data):
    tables_store, df = prepared_data
    # 既に存在するテーブル名を新しいテーブル名として指定
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'TestTable'  # 既に存在するテーブル名
    }
    response = client.post(
        '/api/table/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "newTableName 'TestTable'は既に存在します。"
    assert message == response_data['message']


def test_duplicate_table_empty_table(client, prepared_data):
    tables_store, df = prepared_data
    # 空のテーブルを複製
    empty_df = pl.DataFrame({
        'Col1': [],
        'Col2': []
    })
    tables_store.store_table('EmptyTable', empty_df)
    payload = {
        'tableName': 'EmptyTable',
        'newTableName': 'DuplicatedEmptyTable'
    }
    response = client.post(
        '/api/table/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'DuplicatedEmptyTable'
    # 空のテーブルも正しく複製されることを確認
    duplicated_df = tables_store.get_table(
        'DuplicatedEmptyTable').table
    assert duplicated_df.height == 0
    assert duplicated_df.columns == ['Col1', 'Col2']

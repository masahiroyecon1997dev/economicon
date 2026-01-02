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
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': ['x', 'y', 'z']
        })
        manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_duplicate_table_success(client, tables_manager):
    # 正常にテーブル複製できる
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'DuplicatedTable'
    }
    response = client.post(
        '/api/duplicate-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'],
                     'DuplicatedTable')
    # 複製されたテーブルが存在することを確認
    table_list = tables_manager.get_table_name_list()
    assert 'DuplicatedTable' in table_list
    # 複製されたテーブルの内容が元のテーブルと同じことを確認
    original_df = tables_manager.get_table('TestTable').table
    duplicated_df = tables_manager.get_table('DuplicatedTable').table
    # データフレームの内容が同じかチェック
    assert original_df.equals(duplicated_df)
    # 列名が同じかチェック
    assert original_df.columns == duplicated_df.columns
    # データが同じかチェック
    self.assertEqual(original_df['A'].to_list(),
                     duplicated_df['A'].to_list()
    self.assertEqual(original_df['B'].to_list(),
                     duplicated_df['B'].to_list()
    self.assertEqual(original_df['C'].to_list(),
                     duplicated_df['C'].to_list()


def test_duplicate_table_invalid_source_table(client, tables_manager):
    # 存在しないソーステーブル名
    payload = {
        'tableName': 'NonExistentTable',
        'newTableName': 'DuplicatedTable'
    }
    response = client.post(
        '/api/duplicate-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NonExistentTable' does not exist",
                  response_data['message'])


def test_duplicate_table_existing_destination_table(client, tables_manager):
    # 既に存在するテーブル名を新しいテーブル名として指定
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'TestTable'  # 既に存在するテーブル名
    }
    response = client.post(
        '/api/duplicate-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "newTableName 'TestTable' already exists",
                  response_data['message'])


def test_duplicate_table_empty_table(client, tables_manager):
    # 空のテーブルを複製
    empty_df = pl.DataFrame({
        'Col1': [],
        'Col2': []
    })
    tables_manager.store_table('EmptyTable', empty_df)
    payload = {
        'tableName': 'EmptyTable',
        'newTableName': 'DuplicatedEmptyTable'
    }
    response = client.post(
        '/api/duplicate-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'],
                     'DuplicatedEmptyTable')
    # 空のテーブルも正しく複製されることを確認
    duplicated_df = tables_manager.get_table(
        'DuplicatedEmptyTable').table
    assert duplicated_df.height == 0
    assert duplicated_df.columns == ['Col1', 'Col2']

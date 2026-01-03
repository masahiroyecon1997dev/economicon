import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl

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
        manager.clear_tables()
        # 第1テーブル
        table1_df = pl.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['Tokyo', 'Osaka', 'Kyoto']
        })
        manager.store_table('Table1', table1_df)
        # 第2テーブル
        table2_df = pl.DataFrame({
            'id': [4, 5, 6],
            'name': ['David', 'Eve', 'Frank'],
            'age': [28, 32, 40],
            'city': ['Nagoya', 'Kobe', 'Sendai']
        })
        manager.store_table('Table2', table2_df)
        # 第3テーブル
        table3_df = pl.DataFrame({
            'id': [7, 8],
            'name': ['Grace', 'Henry'],
            'age': [27, 33],
            'city': ['Hiroshima', 'Fukuoka']
        })
        manager.store_table('Table3', table3_df)
        # 列構成が異なるテーブル
        different_table_df = pl.DataFrame({
            'id': [9, 10],
            'username': ['user1', 'user2'],
            'score': [100, 200]
        })
        manager.store_table('DifferentTable', different_table_df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_union_two_tables_all_columns(client, tables_manager):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'name', 'age', 'city']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('UnionTable').table
    assert df.shape == (6, 4
    self.assertListEqual(df['id'].to_list(), [1, 2, 3, 4, 5, 6])
    self.assertListEqual(df['name'].to_list(),
                         ['Alice', 'Bob', 'Charlie',
                          'David', 'Eve', 'Frank'])


def test_union_three_tables_selected_columns(client, tables_manager):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2', 'Table3'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('UnionTable').table
    assert df.shape == (8, 2
    self.assertListEqual(df['id'].to_list(), [1, 2, 3, 4, 5, 6, 7, 8])
    self.assertListEqual(df['name'].to_list(),
                         ['Alice', 'Bob', 'Charlie',
                          'David', 'Eve', 'Frank', 'Grace', 'Henry'])


def test_union_table_name_empty(client, tables_manager):
    payload = {
        'unionTableName': '',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "unionTableName is required.",
                  response_data['message'])


def test_union_table_name_already_exists(client, tables_manager):
    payload = {
        'unionTableName': 'Table1',  # 既存のテーブル名
        'tableNames': ['Table2', 'Table3'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "unionTableName 'Table1' already exists.",
                  response_data['message'])


def test_single_table_in_list(client, tables_manager):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1'],  # 1つのテーブルのみ
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableNames must be with at least 2 tableName.",
                  response_data['message'])


def test_nonexistent_table(client, tables_manager):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'NonExistentTable'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableNames 'NonExistentTable' does not exist.",
                  response_data['message'])


def test_empty_column_names(client, tables_manager):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': []  # 空の列名リスト
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnNames must be with "
                  "at least 1 columnName.",
                  response_data['message'])


def test_nonexistent_column_in_first_table(client, tables_manager):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'nonexistent_column']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnNames 'nonexistent_column' does not exist.",
                  response_data['message'])


def test_column_missing_in_one_table(client, tables_manager):
    payload = {
        'unionTableName': 'UnionTable',
        # DifferentTableには'name'列がない
        'tableNames': ['Table1', 'DifferentTable'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnNames 'name' does not exist.",
                  response_data['message'])


def test_union_preserves_column_order(client, tables_manager):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['name', 'id', 'age']  # 元の順序と異なる
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('UnionTable').table
    # 指定された順序で列が並んでいることを確認
    self.assertListEqual(df.columns, ['name', 'id', 'age'])


def test_missing_request_fields(client, tables_manager):
    # unionTableNameが欠けている場合
    payload = {
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    self.assertEqual(response.status_code,
                     status.HTTP_400_BAD_REQUEST
    # tableNamesが欠けている場合
    payload = {
        'unionTableName': 'UnionTable',
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    self.assertEqual(response.status_code,
                     status.HTTP_400_BAD_REQUEST
    # columnNamesが欠けている場合
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2']
    }
    response = client.post(
        '/api/create-union-table',
        json=payload,
    )
    self.assertEqual(response.status_code,
                     status.HTTP_400_BAD_REQUEST

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


def test_union_two_tables_all_columns(client, tables_store):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'name', 'age', 'city']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_store.get_table('UnionTable').table
    assert df.shape == (6, 4)
    assert df['id'].to_list() == [1, 2, 3, 4, 5, 6]
    assert df['name'].to_list() == [
        'Alice', 'Bob', 'Charlie',
        'David', 'Eve', 'Frank'
    ]


def test_union_three_tables_selected_columns(client, tables_store):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2', 'Table3'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_store.get_table('UnionTable').table
    assert df.shape == (8, 2)
    assert df['id'].to_list() == [1, 2, 3, 4, 5, 6, 7, 8]
    assert df['name'].to_list() == [
        'Alice', 'Bob', 'Charlie',
        'David', 'Eve', 'Frank', 'Grace', 'Henry'
    ]


def test_union_table_name_empty(client, tables_store):
    payload = {
        'unionTableName': '',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data['code'] == 'NG'
    assert "unionTableName は1文字以上である必要があります。" == response_data['message']


def test_union_table_name_already_exists(client, tables_store):
    payload = {
        'unionTableName': 'Table1',  # 既存のテーブル名
        'tableNames': ['Table2', 'Table3'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "unionTableName 'Table1'は既に存在します。"
    assert message == response_data['message']


def test_single_table_in_list(client, tables_store):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1'],  # 1つのテーブルのみ
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "tableNamesは少なくとも 2 つの テーブル名が必要です。"
    assert message == response_data['message']


def test_nonexistent_table(client, tables_store):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'NonExistentTable'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "tableNames 'NonExistentTable'は存在しません。"
    assert message == response_data['message']


def test_empty_column_names(client, tables_store):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': []  # 空の列名リスト
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "columnNamesは少なくとも 1 つの カラム名が必要です。"
    assert message == response_data['message']


def test_nonexistent_column_in_first_table(client, tables_store):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'nonexistent_column']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "columnNames 'nonexistent_column'は存在しません。"
    assert message == response_data['message']


def test_column_missing_in_one_table(client, tables_store):
    payload = {
        'unionTableName': 'UnionTable',
        # DifferentTableには'name'列がない
        'tableNames': ['Table1', 'DifferentTable'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnNames 'name'は存在しません。" == response_data['message']


def test_union_preserves_column_order(client, tables_store):
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['name', 'id', 'age']  # 元の順序と異なる
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_store.get_table('UnionTable').table
    # 指定された順序で列が並んでいることを確認
    assert list(df.columns) == ['name', 'id', 'age']


def test_missing_request_fields(client, tables_store):
    # unionTableNameが欠けている場合
    payload = {
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # # tableNamesが欠けている場合
    payload = {
        'unionTableName': 'UnionTable',
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # # columnNamesが欠けている場合
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': ['Table1', 'Table2']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# Pydanticバリデーションテスト


def test_create_union_table_pydantic_empty_union_table_name(client, tables_store):
    """
    unionTableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        'unionTableName': '',
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'unionTableName' in response_data['message']


def test_create_union_table_pydantic_empty_table_names(client, tables_store):
    """
    tableNamesが空の場合はバリデーションエラーになる
    """
    payload = {
        'unionTableName': 'UnionTable',
        'tableNames': [],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'List should have at least 1 item' in response_data['message']


def test_create_union_table_pydantic_missing_union_table_name(client, tables_store):
    """
    unionTableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {
        'tableNames': ['Table1', 'Table2'],
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'unionTableName' in response_data['message']


def test_create_union_table_pydantic_missing_table_names(client, tables_store):
    """
    tableNamesが欠損している場合はバリデーションエラーになる
    """
    payload = {
        'unionTableName': 'UnionTable',
        'columnNames': ['id', 'name']
    }
    response = client.post(
        '/api/table/create-union',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'tableNames' in response_data['message']

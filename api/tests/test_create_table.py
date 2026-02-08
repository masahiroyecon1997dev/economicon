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
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_create_table_success(client, tables_store):
    payload = {
        'tableName': 'NewTable',
        'tableNumberOfRows': 3,
        'columnNames': ['A', 'B']
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # テーブルが作成されているか
    assert 'NewTable' in tables_store.get_table_name_list()
    df = tables_store.get_table('NewTable').table
    assert df.shape == (3, 2)
    assert df.columns == ['A', 'B']
    assert df['A'].to_list() == [None, None, None]


def test_create_table_invalid_table_name(client, tables_store):
    # テーブル名が空
    payload = {
        'tableName': '',
        'tableNumberOfRows': 2,
        'columnNames': ['A', 'B']
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data['code'] == 'NG'
    assert "tableName は1文字以上である必要があります。" == response_data['message']


def test_create_table_invalid_number_of_rows(client, tables_store):
    # テーブル行数が文字列
    payload = {
        'tableName': 'EmptyRowTable',
        'tableNumberOfRows': 'A',
        'columnNames': ['A', 'B']
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert response_data['code'] == 'NG'
    # assert "tableNumberOfRows must be a number." == response_data['message']


def test_create_table_invalid_columns(client, tables_store):
    # columnsが空
    payload = {
        'tableName': 'EmptyColTable',
        'tableNumberOfRows': 2,
        'columnNames': []
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data['code'] == 'NG'
    message = "List should have at least 1 item after validation, not 0"
    assert message == response_data['message']


# Pydanticバリデーションテスト


def test_create_table_pydantic_empty_table_name(client, tables_store):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        'tableName': '',
        'tableNumberOfRows': 3,
        'columnNames': ['A', 'B']
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'tableName' in response_data['message']


def test_create_table_pydantic_negative_number_of_rows(client, tables_store):
    """
    tableNumberOfRowsが負の場合はバリデーションエラーになる
    """
    payload = {
        'tableName': 'TestTable',
        'tableNumberOfRows': -1,
        'columnNames': ['A', 'B']
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'tableNumberOfRows' in response_data['message']


def test_create_table_pydantic_empty_column_names(client, tables_store):
    """
    columnNamesが空の場合はバリデーションエラーになる
    """
    payload = {
        'tableName': 'TestTable',
        'tableNumberOfRows': 3,
        'columnNames': []
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'List should have at least 1 item' in response_data['message']


def test_create_table_pydantic_missing_table_name(client, tables_store):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {
        'tableNumberOfRows': 3,
        'columnNames': ['A', 'B']
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'tableName' in response_data['message']


def test_create_table_pydantic_missing_number_of_rows(client, tables_store):
    """
    tableNumberOfRowsが欠損している場合はバリデーションエラーになる
    """
    payload = {
        'tableName': 'TestTable',
        'columnNames': ['A', 'B']
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'tableNumberOfRows' in response_data['message']


def test_create_table_pydantic_missing_column_names(client, tables_store):
    """
    columnNamesが欠損している場合はバリデーションエラーになる
    """
    payload = {
        'tableName': 'TestTable',
        'tableNumberOfRows': 3
    }
    response = client.post(
        '/api/table/create',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'columnNames' in response_data['message']

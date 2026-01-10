import pytest
from analysisapp.services.data.tables_manager import TablesManager
from fastapi import status
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_create_table_success(client, tables_manager):
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
    assert 'NewTable' in tables_manager.get_table_name_list()
    df = tables_manager.get_table('NewTable').table
    assert df.shape == (3, 2)
    assert df.columns == ['A', 'B']
    assert df['A'].to_list() == [None, None, None]


def test_create_table_invalid_table_name(client, tables_manager):
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
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName is required." == response_data['message']


def test_create_table_invalid_number_of_rows(client, tables_manager):
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


def test_create_table_invalid_columns(client, tables_manager):
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
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "columnNames must be with at least 1 item."
    assert message == response_data['message']

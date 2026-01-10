import polars as pl
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
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2, 3, 4, 5, 6, 7, 1, 2, 3],
        'B': [4, 5, 6, 7, 8, 9, 10, 4, 5, 6]
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_input_cell_data_success(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'columnName': 'A',
        'rowIndex': 2,
        'newValue': 99
    }
    response = client.post(
        '/api/operation/input-cell-data',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('TestTable').table
    assert df['A'][1] == 99


def test_input_cell_data_success_with_string(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'columnName': 'A',
        'rowIndex': 1,
        'newValue': 'AAA'
    }
    response = client.post(
        '/api/operation/input-cell-data',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('TestTable').table
    assert df['A'][0] == 'AAA'


def test_input_cell_data_invalid_table(client, tables_manager):
    payload = {
        'tableName': 'NoTable',
        'columnName': 'A',
        'rowIndex': 0,
        'newValue': 10
    }
    response = client.post(
        '/api/operation/input-cell-data',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable' does not exist." == response_data['message']


def test_input_cell_data_invalid_column(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'columnName': 'Z',
        'rowIndex': 0,
        'newValue': 10
    }
    response = client.post(
        '/api/operation/input-cell-data',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName 'Z' does not exist." in response_data['message']


def test_input_cell_data_invalid_row_over(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'columnName': 'A',
        'rowIndex': 100,
        'newValue': 10
    }
    response = client.post(
        '/api/operation/input-cell-data',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "rowIndex must be between 1 and 10." == response_data['message']


def test_input_cell_data_invalid_row_string(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'columnName': 'A',
        'rowIndex': 'String',
        'newValue': 10
    }
    response = client.post(
        '/api/operation/input-cell-data',
        json=payload,
    )
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert response_data['code'] == 'NG'
    # assert "rowIndex must be an integer." == response_data['message']

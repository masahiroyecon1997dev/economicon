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
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2, 3, 4, 5, 6, 7, 1, 2, 3],
        'B': [11, 12, 30, 40, 1, 2, 3, 40, 10, 2],
        'C': [1, 1, 4, 8, 4, 6, 7, 2, 3, 2]
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_filter_equals(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'A',
        'condition': 'equals',
        'isCompareColumn': 'false',
        'compareValue': 2
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    assert df.shape[0] == 2
    assert df['A'].to_list() == [2, 2]


def test_filter_greater_than(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'B',
        'condition': 'greaterThan',
        'isCompareColumn': 'false',
        'compareValue': 10
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    assert df.shape[0] == 5
    assert df['B'].to_list() == [11, 12, 30, 40, 40]


def test_filter_not_equals(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'A',
        'condition': 'notEquals',
        'isCompareColumn': 'false',
        'compareValue': 2
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    assert df.shape[0] == 8
    assert 2 not in df['A'].to_list()


def test_filter_greater_than_or_equals(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'B',
        'condition': 'greaterThanOrEquals',
        'isCompareColumn': 'false',
        'compareValue': 30
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    assert df.shape[0] == 3
    assert df['B'].to_list() == [30, 40, 40]


def test_filter_less_than(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'A',
        'condition': 'lessThan',
        'isCompareColumn': 'false',
        'compareValue': 3
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    assert df.shape[0] == 4
    assert df['A'].to_list() == [1, 2, 1, 2]


def test_filter_less_than_or_equals(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'B',
        'condition': 'lessThanOrEquals',
        'isCompareColumn': 'false',
        'compareValue': 12
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    assert df.shape[0] == 7
    assert df['B'].to_list() == [11, 12, 1, 2, 3, 10, 2]


def test_filter_equals_compare_column(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'A',
        'condition': 'equals',
        'isCompareColumn': 'true',
        'compareValue': 'C'
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    # A==Cとなる行
    assert df.shape[0] == 3
    assert df['A'].to_list() == [1, 6, 7]
    assert df['C'].to_list() == [1, 6, 7]


def test_filter_greater_than_compare_column(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'A',
        'condition': 'greaterThan',
        'isCompareColumn': 'true',
        'compareValue': 'C'
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    # B>Cとなる行
    assert df.shape[0] == 3
    assert df['A'].to_list() == [2, 5, 3]
    assert df['C'].to_list() == [1, 4, 2]


def test_filter_less_than_or_equals_compare_column(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'A',
        'condition': 'lessThanOrEquals',
        'isCompareColumn': 'true',
        'compareValue': 'C'
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('FilteredTable').table
    # A<=C
    assert df.shape[0] == 7
    assert df['A'].to_list() == [1, 3, 4, 6, 7, 1, 2]
    assert df['C'].to_list() == [1, 4, 8, 6, 7, 2, 3]


def test_filter_invalid_table(client, tables_manager):
    payload = {
        'tableName': 'NoTable',
        'newTableName': 'FilteredTable',
        'columnName': 'A',
        'condition': 'equals',
        'isCompareColumn': 'false',
        'compareValue': 1
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable' does not exist." == response_data['message']


def test_filter_invalid_column(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'Z',
        'condition': 'equals',
        'isCompareColumn': 'false',
        'compareValue': 1
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName 'Z' does not exist." == response_data['message']


def test_filter_invalid_condition(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'newTableName': 'FilteredTable',
        'columnName': 'A',
        'condition': 'invalid_condition',
        'isCompareColumn': 'false',
        'compareValue': 1
    }
    response = client.post(
        '/api/operation/filter-single-condition',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "condition 'invalid_condition' is not supported. Supported condition: equals, notEquals, greaterThan, lessThan, greaterThanOrEquals, lessThanOrEquals" == response_data['message']

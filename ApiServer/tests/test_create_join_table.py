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
        # テーブルをクリア
        manager.clear_tables()
        # 左テーブル
        left_df = pl.DataFrame({
            'id': [1, 2, 3, 4],
            'val_left': ['A', 'B', 'C', 'D']
        })
        manager.store_table('LeftTable', left_df)
        # 右テーブル
        right_df = pl.DataFrame({
            'id': [3, 4, 5, 6],
            'val_right': ['X', 'Y', 'Z', 'W']
        })
        manager.store_table('RightTable', right_df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_inner_join(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'LeftTable',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'inner'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('JoinTable').table
    assert df.shape == (2, 3
    self.assertListEqual(df['id'].to_list(), [3, 4])
    self.assertListEqual(df['val_left'].to_list(), ['C', 'D'])
    self.assertListEqual(df['val_right'].to_list(), ['X', 'Y'])


def test_left_join(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'LeftTable',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'left'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('JoinTable').table
    assert df.shape == (4, 3
    self.assertListEqual(df['id'].to_list(), [1, 2, 3, 4])
    self.assertListEqual(df['val_left'].to_list(), ['A', 'B', 'C', 'D'])
    self.assertListEqual(df['val_right'].to_list(), [None, None, 'X', 'Y'])


def test_right_join(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'LeftTable',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'right'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('JoinTable').table
    assert df.shape == (4, 3
    self.assertListEqual(df['id'].to_list(), [3, 4, 5, 6])
    self.assertListEqual(df['val_left'].to_list(), ['C', 'D', None, None])
    self.assertListEqual(df['val_right'].to_list(), ['X', 'Y', 'Z', 'W'])


def test_outer_join(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'LeftTable',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'outer'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('JoinTable').table
    assert df.shape == (6, 3
    self.assertListEqual(df['id'].to_list(), [1, 2, 3, 4, 5, 6])
    self.assertListEqual(df['val_left'].to_list(), ['A', 'B', 'C', 'D',
                                                    None, None])
    self.assertListEqual(df['val_right'].to_list(), [None, None, 'X', 'Y',
                                                     'Z', 'W'])


def test_join_table_name_empty(client, tables_manager):
    payload = {
        'joinTableName': '',
        'leftTableName': 'LeftTable',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'inner'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert response_data['message'], "joinTableName is required.")


def test_left_table_not_found(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'NotExist',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'inner'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "leftTableName 'NotExist' does not exist." in response_data['message']


def test_right_table_not_found(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'LeftTable',
        'rightTableName': 'NotExist',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'inner'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "rightTableName 'NotExist' does not exist." in response_data['message']


def test_left_key_column_not_found(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'LeftTable',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['not_exist_col'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'inner'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "leftKeyColumnNames 'not_exist_col' does not exist." in response_data['message']


def test_right_key_column_not_found(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'LeftTable',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['not_exist_col'],
        'joinType': 'inner'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "rightKeyColumnNames 'not_exist_col' does not exist." in response_data['message']


def test_invalid_join_type(client, tables_manager):
    payload = {
        'joinTableName': 'JoinTable',
        'leftTableName': 'LeftTable',
        'rightTableName': 'RightTable',
        'leftKeyColumnNames': ['id'],
        'rightKeyColumnNames': ['id'],
        'joinType': 'invalid_type'
    }
    response = client.post(
        '/api/create-join-table',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "joinType 'invalid_type' is not supported. " in response_data['message']
                  "Supported joinType: inner, left, right, outer")

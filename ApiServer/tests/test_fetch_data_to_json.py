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
        # テスト用のテーブルをセットアップ
    manager = TablesManager()
        # テーブルをクリア
        manager.clear_tables()
        self.table_name = "test_table"
        self.test_data = pl.DataFrame({
            "column1": [1, 2, 3, 4, 5],
            "column2": ["a", "b", "c", "d", "e"]
        })
        manager.store_table(self.table_name, self.test_data)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_fetch_data_to_json_success(client, tables_manager):
    # 正常系テスト: JSONデータを取得
    start_row = 2
    fetch_rows = 2
    response = client.get(
        f'/api/fetch-data-to-json?tableName={self.table_name}'
        f'&startRow={start_row}&fetchRows={fetch_rows}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data["result"]["tableName"], self.table_name)
    # メタ情報の確認
    assert response_data["result"]["totalRows"], 5)
    assert response_data["result"]["startRow"], start_row)
    assert response_data["result"]["endRow"],
                     start_row + fetch_rows - 1)
    # データの内容を確認
    data = response_data["result"]["data"]
    expected_data = self.test_data[1:3].write_json()
    assert data == expected_data


def test_fetch_data_to_json_table_not_found(client, tables_manager):
    # 異常系テスト: 存在しないテーブル名
    not_existent_table = "non_existent_table"
    start_row = 1
    fetch_rows = 3
    response = client.get(
        f'/api/fetch-data-to-json?tableName={not_existent_table}'
        f'&startRow={start_row}&fetchRows={fetch_rows}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "tableName 'non_existent_table' does not exist." in response_data['message']


def test_fetch_data_to_json_invalid_start_row_range(client, tables_manager):
    # 異常系テスト: 無効な行範囲 startRow
    start_row = 0
    fetch_rows = 4
    response = client.get(
        f'/api/fetch-data-to-json?tableName={self.table_name}'
        f'&startRow={start_row}&fetchRows={fetch_rows}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "startRow must be between 1 and 5." in response_data['message']


def test_fetch_data_to_json_invalid_fetch_rows(client, tables_manager):
    # 異常系テスト: 無効な取得行数 fetchRows
    start_row = 1
    fetch_rows = 0
    response = client.get(
        f'/api/fetch-data-to-json?tableName={self.table_name}'
        f'&startRow={start_row}&fetchRows={fetch_rows}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "fetchRows must be a positive integer." in response_data['message']


def test_fetch_data_to_json_missing_table_name(client, tables_manager):
    # 異常系テスト: 必須パラメータが不足している場合（tableName）
    not_table_name = ""
    start_row = 1
    fetch_rows = 6
    response = client.get(
        f'/api/fetch-data-to-json?tableName={not_table_name}'
        f'&startRow={start_row}&fetchRows={fetch_rows}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "tableName is required." in response_data['message']


def test_fetch_data_to_json_missing_start_row(client, tables_manager):
    # 異常系テスト: 必須パラメータが不足している場合（startRow）
    start_row = ""
    fetch_rows = 6
    response = client.get(
        f'/api/fetch-data-to-json?tableName={self.table_name}'
        f'&startRow={start_row}&fetchRows={fetch_rows}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "startRow is required." in response_data['message']


def test_fetch_data_to_json_missing_fetch_rows(client, tables_manager):
    # 異常系テスト: 必須パラメータが不足している場合（fetchRows）
    start_row = 1
    fetch_rows = ""
    response = client.get(
        f'/api/fetch-data-to-json?tableName={self.table_name}'
        f'&startRow={start_row}&fetchRows={fetch_rows}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "fetchRows is required." in response_data['message']


def test_fetch_data_to_json_fetch_beyond_table(client, tables_manager):
    # 正常系テスト: テーブルの行数を超える取得行数
    start_row = 3
    fetch_rows = 10  # テーブルは5行なので3行目から最後までの3行を取得
    response = client.get(
        f'/api/fetch-data-to-json?tableName={self.table_name}'
        f'&startRow={start_row}&fetchRows={fetch_rows}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # メタ情報の確認
    assert response_data["result"]["totalRows"], 5)
    assert response_data["result"]["startRow"], start_row)
    assert response_data["result"]["endRow"], 5)  # 最後の行
    # データの内容を確認（3行目から最後まで）
    data = response_data["result"]["data"]
    expected_data = self.test_data[2:5].write_json()
    assert data == expected_data

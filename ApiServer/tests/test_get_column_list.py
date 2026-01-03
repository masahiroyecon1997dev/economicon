import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl

from main import app
from analysisapp.services.data.tables_manager import TablesManager


table_name = "test_table"
# 作成するテーブルは2カラムとする
test_data = pl.DataFrame({
    "col1": [1, 2, 3],
    "col2": ["a", "b", "c"],
    "col3": [1.1, 2.2, 3.3]
})

@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    manager.clear_tables()
    manager.store_table(table_name, test_data)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_get_column_info_list_success(client, tables_manager):
    # 正常系テスト：テーブルが存在する場合
    response = client.get(f'/api/get-column-list'
                               f'?tableName={table_name}',
                               )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['tableName'] == table_name
    # カラム名はDataFrameのスキーマ順に返ると想定
    expected_columns = [{'name': name, 'type': str(dtype)}
                        for name, dtype
                        in test_data.schema.items()]
    assert result['columnInfoList'] == expected_columns


def test_get_column_info_list_number_success(client, tables_manager):
    # 正常系テスト：テーブルが存在する場合（数値型の列のみ）
    response = client.get(f'/api/get-column-list'
                               f'?tableName={table_name}'
                               f'&isNumberOnly=true',
                               )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['tableName'] == table_name
    # カラム名はDataFrameのスキーマ順に返ると想定
    expected_columns = [{'name': name, 'type': str(dtype)}
                        for name, dtype
                        in test_data.schema.items()
                        if dtype.is_numeric()]
    assert result['columnInfoList'] == expected_columns


def test_get_column_info_list_table_not_found(client, tables_manager):
    # 異常系テスト：存在しないテーブル名の場合
    non_existent_table_name = "non_existent_table"
    response = client.get('/api/get-column-list'
                               f'?tableName={non_existent_table_name}',
                               )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # エラーメッセージにテーブル名が存在しない旨が含まれることを確認
    assert "tableName 'non_existent_table' does not exist" == response_data['message']


def test_get_column_info_list_exception(client, tables_manager):
    # 例外発生時のテスト
    # TablesManager.get_column_info_list を一時的に例外を投げるようにモンキーパッチ
    original_method = tables_manager.get_column_info_list
    def raise_exception(table_name: str) -> pl.Schema:
        raise Exception("DB error")
    tables_manager.get_column_info_list = raise_exception
    response = client.get(f'/api/get-column-list'
                               f'?tableName={table_name}',
                               )
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    assert "An unexpected error during getting column info list." == response_data['message']
    # 後始末
    tables_manager.get_column_info_list = original_method

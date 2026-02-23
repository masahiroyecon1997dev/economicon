import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.tables_store import TablesStore
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame(
        {
            "group": ["A", "A", "A", "B", "B", "B"],
            "time": [1, 2, 3, 1, 2, 3],
            "value": [10, 20, 30, 40, 50, 60],
        }
    )
    manager.store_table("TestTable", df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_add_lag_column_success_no_group(client, tables_store):
    # グループなしでラグ変数を追加
    payload = {
        "tableName": "TestTable",
        "sourceColumn": "value",
        "newColumnName": "value_lag1",
        "periods": -1,
        "groupColumns": [],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # ラグ変数が正しく追加されているか確認
    df = tables_store.get_table("TestTable").table
    assert "value_lag1" in df.columns
    lag_values = df["value_lag1"].to_list()
    # 最初の値はNone、以降は前の値
    expected = [None, 10, 20, 30, 40, 50]
    assert lag_values == expected


def test_add_lead_column_success_no_group(client, tables_store):
    # グループなしでリード変数を追加
    payload = {
        "tableName": "TestTable",
        "sourceColumn": "value",
        "newColumnName": "value_lead1",
        "periods": 1,
        "groupColumns": [],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # リード変数が正しく追加されているか確認
    df = tables_store.get_table("TestTable").table
    assert "value_lead1" in df.columns
    lead_values = df["value_lead1"].to_list()
    # 次の値、最後はNone
    expected = [20, 30, 40, 50, 60, None]
    assert lead_values == expected


def test_add_lag_column_success_with_group(client, tables_store):
    # グループありでラグ変数を追加
    payload = {
        "tableName": "TestTable",
        "sourceColumn": "value",
        "newColumnName": "value_lag1_grouped",
        "periods": -1,
        "groupColumns": ["group"],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # グループ内でのラグ変数が正しく追加されているか確認
    df = tables_store.get_table("TestTable").table
    assert "value_lag1_grouped" in df.columns
    lag_values = df["value_lag1_grouped"].to_list()
    # 各グループの最初の値はNone
    expected = [None, 10, 20, None, 40, 50]
    assert lag_values == expected


def test_add_lead_column_success_with_group(client, tables_store):
    # グループありでリード変数を追加
    payload = {
        "tableName": "TestTable",
        "sourceColumn": "value",
        "newColumnName": "value_lead1_grouped",
        "periods": 1,
        "groupColumns": ["group"],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # グループ内でのリード変数が正しく追加されているか確認
    df = tables_store.get_table("TestTable").table
    assert "value_lead1_grouped" in df.columns
    lead_values = df["value_lead1_grouped"].to_list()
    # 各グループの最後の値はNone
    expected = [20, 30, None, 50, 60, None]
    assert lead_values == expected


def test_add_lag_lead_column_invalid_table(client, tables_store):
    # 存在しないテーブル名
    payload = {
        "tableName": "NoTable",
        "sourceColumn": "value",
        "newColumnName": "value_lag1",
        "periods": -1,
        "groupColumns": [],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert "tableName 'NoTable'は存在しません。" == response_data["message"]


def test_add_lag_lead_column_invalid_source_column(client, tables_store):
    # 存在しないソース列名
    payload = {
        "tableName": "TestTable",
        "sourceColumn": "nonexistent",
        "newColumnName": "value_lag1",
        "periods": -1,
        "groupColumns": [],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = "sourceColumn 'nonexistent'は存在しません。"
    assert message == response_data["message"]


def test_add_lag_lead_column_invalid_group_column(client, tables_store):
    # 存在しないグループ列名
    payload = {
        "tableName": "TestTable",
        "sourceColumn": "value",
        "newColumnName": "value_lag1",
        "periods": -1,
        "groupColumns": ["nonexistent"],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = "groupColumns 'nonexistent'は存在しません。"
    assert message == response_data["message"]


def test_add_lag_lead_column_existing_column_name(client, tables_store):
    # 既存の列名を新しい列名として指定
    payload = {
        "tableName": "TestTable",
        "sourceColumn": "value",
        "newColumnName": "group",  # 既存の列名
        "periods": -1,
        "groupColumns": [],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert (
        "newColumnName 'group'は既に存在します。" == response_data["message"]
    )


def test_add_lag_lead_column_multiple_periods(client, tables_store):
    # 複数期間のラグを追加
    payload = {
        "tableName": "TestTable",
        "sourceColumn": "value",
        "newColumnName": "value_lag2",
        "periods": -2,
        "groupColumns": [],
    }
    response = client.post(
        "/api/column/add-lag-lead",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # 2期間ラグが正しく追加されているか確認
    df = tables_store.get_table("TestTable").table
    assert "value_lag2" in df.columns
    lag_values = df["value_lag2"].to_list()
    # 最初の2つの値はNone
    expected = [None, None, 10, 20, 30, 40]
    assert lag_values == expected

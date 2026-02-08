import polars as pl
import pytest
from economicon.services.data.tables_store import TablesStore
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
    # テーブルをクリア
    manager.clear_tables()
    # 左テーブル
    left_df = pl.DataFrame(
        {"id": [1, 2, 3, 4], "val_left": ["A", "B", "C", "D"]}
    )
    manager.store_table("LeftTable", left_df)
    # 右テーブル
    right_df = pl.DataFrame(
        {"id": [3, 4, 5, 6], "val_right": ["X", "Y", "Z", "W"]}
    )
    manager.store_table("RightTable", right_df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_inner_join(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    assert df.shape == (2, 3)
    assert df["id"].to_list() == [3, 4]
    assert df["val_left"].to_list() == ["C", "D"]
    assert df["val_right"].to_list() == ["X", "Y"]


def test_left_join(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "left",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    assert df.shape == (4, 3)
    assert df["id"].to_list() == [1, 2, 3, 4]
    assert df["val_left"].to_list() == ["A", "B", "C", "D"]
    assert df["val_right"].to_list() == [None, None, "X", "Y"]


def test_right_join(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "right",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    assert df.shape == (4, 3)
    assert df["id"].to_list() == [3, 4, 5, 6]
    assert df["val_left"].to_list() == ["C", "D", None, None]
    assert df["val_right"].to_list() == ["X", "Y", "Z", "W"]


def test_outer_join(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "outer",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("JoinTable").table
    assert df.shape == (6, 3)
    assert df["id"].to_list() == [1, 2, 3, 4, 5, 6]
    assert df["val_left"].to_list() == ["A", "B", "C", "D", None, None]
    assert df["val_right"].to_list() == [None, None, "X", "Y", "Z", "W"]


def test_join_table_name_empty(client, tables_store):
    payload = {
        "joinTableName": "",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "NG"
    assert (
        "joinTableName は1文字以上である必要があります。"
        == response_data["message"]
    )


def test_left_table_not_found(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "NotExist",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = "leftTableName 'NotExist'は存在しません。"
    assert message == response_data["message"]


def test_right_table_not_found(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "NotExist",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = "rightTableName 'NotExist'は存在しません。"
    assert message == response_data["message"]


def test_left_key_column_not_found(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["not_exist_col"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = "leftKeyColumnNames 'not_exist_col'は存在しません。"
    assert message == response_data["message"]


def test_right_key_column_not_found(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["not_exist_col"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = "rightKeyColumnNames 'not_exist_col'は存在しません。"
    assert message == response_data["message"]


def test_invalid_join_type(client, tables_store):
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "invalid_type",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = (
        "joinType 'invalid_type'はサポートされていません。"
        "サポートされるjoinType: inner, left, right, outer"
    )
    assert message == response_data["message"]


# Pydanticバリデーションテスト


def test_create_join_table_pydantic_empty_join_table_name(
    client, tables_store
):
    """
    joinTableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "joinTableName" in response_data["message"]


def test_create_join_table_pydantic_empty_left_table_name(
    client, tables_store
):
    """
    leftTableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "leftTableName" in response_data["message"]


def test_create_join_table_pydantic_empty_right_table_name(
    client, tables_store
):
    """
    rightTableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "rightTableName" in response_data["message"]


def test_create_join_table_pydantic_empty_join_type(client, tables_store):
    """
    joinTypeが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "joinType" in response_data["message"]


def test_create_join_table_pydantic_empty_left_key_column_names(
    client, tables_store
):
    """
    leftKeyColumnNamesが空の場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": [],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "List should have at least 1 item" in response_data["message"]


def test_create_join_table_pydantic_empty_right_key_column_names(
    client, tables_store
):
    """
    rightKeyColumnNamesが空の場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": [],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "List should have at least 1 item" in response_data["message"]


def test_create_join_table_pydantic_missing_join_table_name(
    client, tables_store
):
    """
    joinTableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "joinTableName" in response_data["message"]


def test_create_join_table_pydantic_missing_left_table_name(
    client, tables_store
):
    """
    leftTableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "leftTableName" in response_data["message"]


def test_create_join_table_pydantic_missing_right_table_name(
    client, tables_store
):
    """
    rightTableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "rightTableName" in response_data["message"]


def test_create_join_table_pydantic_missing_left_key_column_names(
    client, tables_store
):
    """
    leftKeyColumnNamesが欠損している場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "rightKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "leftKeyColumnNames" in response_data["message"]


def test_create_join_table_pydantic_missing_right_key_column_names(
    client, tables_store
):
    """
    rightKeyColumnNamesが欠損している場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "joinType": "inner",
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "rightKeyColumnNames" in response_data["message"]


def test_create_join_table_pydantic_missing_join_type(client, tables_store):
    """
    joinTypeが欠損している場合はバリデーションエラーになる
    """
    payload = {
        "joinTableName": "JoinTable",
        "leftTableName": "LeftTable",
        "rightTableName": "RightTable",
        "leftKeyColumnNames": ["id"],
        "rightKeyColumnNames": ["id"],
    }
    response = client.post(
        "/api/table/create-join",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "joinType" in response_data["message"]

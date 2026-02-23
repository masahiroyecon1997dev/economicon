import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ─────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────
MAX_TABLE_NAME_LENGTH = 128

# ベースペイロード（正常系共通）
_BASE_PAYLOAD: dict = {
    "tableName": "TestTable",
    "rowCount": 5,
    "simulationColumns": [
        {
            "columnName": "col1",
            "distribution": {"type": "normal", "loc": 0.0, "scale": 1.0},
        }
    ],
}

# 単独カラム設定（正規分布）
_COL_NORMAL = {
    "columnName": "normal_col",
    "distribution": {"type": "normal", "loc": 0.0, "scale": 1.0},
}
# 単独カラム設定（一様分布）
_COL_UNIFORM = {
    "columnName": "uniform_col",
    "distribution": {"type": "uniform", "low": 0.0, "high": 10.0},
}
# 単独カラム設定（指数分布）
_COL_EXP = {
    "columnName": "exp_col",
    "distribution": {"type": "exponential", "scale": 2.0},
}
# 単独カラム設定（固定値）
_COL_FIXED = {
    "columnName": "fixed_col",
    "distribution": {"type": "fixed", "value": 42.0},
}


# ─────────────────────────────────────────────────────────────
# フィクスチャ
# ─────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    yield manager
    manager.clear_tables()


# ─────────────────────────────────────────────────────────────
# 正常系：各分布タイプ
# ─────────────────────────────────────────────────────────────
def test_create_table_with_normal_distribution(client, tables_store):
    """正規分布カラムを持つテーブルを正常に作成できる"""
    payload = {
        "tableName": "NormalTable",
        "rowCount": 100,
        "simulationColumns": [_COL_NORMAL],
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "NormalTable"
    df = tables_store.get_table("NormalTable").table
    assert len(df) == 100
    assert "normal_col" in df.columns


def test_create_table_with_uniform_distribution(client, tables_store):
    """一様分布カラムを持つテーブルを正常に作成できる"""
    payload = {
        "tableName": "UniformTable",
        "rowCount": 50,
        "simulationColumns": [_COL_UNIFORM],
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("UniformTable").table
    assert len(df) == 50
    assert "uniform_col" in df.columns


def test_create_table_with_exponential_distribution(client, tables_store):
    """指数分布カラムを持つテーブルを正常に作成できる"""
    payload = {
        "tableName": "ExpTable",
        "rowCount": 30,
        "simulationColumns": [_COL_EXP],
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("ExpTable").table
    assert len(df) == 30


def test_create_table_with_fixed_distribution(client, tables_store):
    """固定値カラムを持つテーブルを正常に作成できる"""
    payload = {
        "tableName": "FixedTable",
        "rowCount": 10,
        "simulationColumns": [_COL_FIXED],
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FixedTable").table
    assert len(df) == 10
    assert "fixed_col" in df.columns
    # 全行が固定値 42.0 であることを確認
    assert (df["fixed_col"] == 42.0).all()


def test_create_table_with_multiple_columns(client, tables_store):
    """複数カラムを持つテーブルを正常に作成できる"""
    payload = {
        "tableName": "MultiTable",
        "rowCount": 20,
        "simulationColumns": [_COL_NORMAL, _COL_UNIFORM, _COL_EXP],
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("MultiTable").table
    assert len(df) == 20
    assert len(df.columns) == 3
    assert "normal_col" in df.columns
    assert "uniform_col" in df.columns
    assert "exp_col" in df.columns


# ─────────────────────────────────────────────────────────────
# 異常系 400：重複テーブル名
# ─────────────────────────────────────────────────────────────
def test_create_simulation_data_table_duplicate_table_name(
    client, tables_store
):
    """既存テーブル名と重複する場合は 400 DATA_ALREADY_EXISTS"""
    # 先に作成
    client.post("/api/table/create-simulation-data", json=_BASE_PAYLOAD)
    # 同じ名前で再作成
    response = client.post(
        "/api/table/create-simulation-data", json=_BASE_PAYLOAD
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"] == "tableName 'TestTable'は既に存在します。"
    )
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（空・0値）
# ─────────────────────────────────────────────────────────────
def test_create_simulation_data_table_pydantic_empty_table_name(
    client, tables_store
):
    """tableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": ""}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]


def test_create_simulation_data_table_pydantic_zero_row_count(
    client, tables_store
):
    """rowCountが0の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rowCount": 0}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは1以上で入力してください。"
    assert response_data["details"] == ["rowCountは1以上で入力してください。"]


def test_create_simulation_data_table_pydantic_negative_row_count(
    client, tables_store
):
    """rowCountが負の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "rowCount": -1}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは1以上で入力してください。"
    assert response_data["details"] == ["rowCountは1以上で入力してください。"]


def test_create_simulation_data_table_pydantic_empty_simulation_columns(
    client, tables_store
):
    """simulationColumnsが空リストの場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "simulationColumns": []}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "simulationColumnsは1件以上ある必要があります。"
    )
    assert response_data["details"] == [
        "simulationColumnsは1件以上ある必要があります。"
    ]


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー（必須項目欠損）
# ─────────────────────────────────────────────────────────────
def test_create_simulation_data_table_pydantic_missing_table_name(
    client, tables_store
):
    """tableNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "tableName"}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "tableNameは必須項目です。"
    assert response_data["details"] == ["tableNameは必須項目です。"]


def test_create_simulation_data_table_pydantic_missing_row_count(
    client, tables_store
):
    """rowCountが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "rowCount"}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "rowCountは必須項目です。"
    assert response_data["details"] == ["rowCountは必須項目です。"]


def test_create_simulation_data_table_pydantic_missing_simulation_columns(
    client, tables_store
):
    """simulationColumnsが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {
        k: v for k, v in _BASE_PAYLOAD.items() if k != "simulationColumns"
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "simulationColumnsは必須項目です。"
    assert response_data["details"] == ["simulationColumnsは必須項目です。"]


def test_create_simulation_data_table_pydantic_missing_column_name(
    client, tables_store
):
    """columnNameが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {
        **_BASE_PAYLOAD,
        "simulationColumns": [
            {"distribution": {"type": "normal", "loc": 0.0, "scale": 1.0}}
        ],
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "simulationColumns.0.columnNameは必須項目です。"
    )
    assert response_data["details"] == [
        "simulationColumns.0.columnNameは必須項目です。"
    ]


def test_create_simulation_data_table_pydantic_missing_distribution(
    client, tables_store
):
    """distributionが欠損している場合は 422 VALIDATION_ERROR"""
    payload = {
        **_BASE_PAYLOAD,
        "simulationColumns": [{"columnName": "col1"}],
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "simulationColumns.0.distributionは必須項目です。"
    )
    assert response_data["details"] == [
        "simulationColumns.0.distributionは必須項目です。"
    ]


def test_create_simulation_data_table_pydantic_invalid_distribution_type(
    client, tables_store
):
    """無効な distribution.type の場合は 422 VALIDATION_ERROR"""
    payload = {
        **_BASE_PAYLOAD,
        "simulationColumns": [
            {"columnName": "col1", "distribution": {"type": "invalid_type"}}
        ],
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    # メッセージはPydanticの判別ユニオンエラーをそのまま使用
    assert "invalid_type" in response_data["message"]


# ─────────────────────────────────────────────────────────────
# 意地悪テスト（N1-N7）
# ─────────────────────────────────────────────────────────────
def test_n1_table_name_japanese(client, tables_store):
    """N1: tableNameに日本語を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "シミュレーションテーブル"}
    response = client.post("/api/table/create-simulation-data", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n2_table_name_emoji(client, tables_store):
    """N2: tableNameに絵文字を使っても正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "SimTable🎲"}
    response = client.post("/api/table/create-simulation-data", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n3_table_name_surrounding_spaces(client, tables_store):
    """N3: tableNameの前後スペースはトリムされ正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "  TestTable  "}
    response = client.post("/api/table/create-simulation-data", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n4_table_name_max_length(client, tables_store):
    """N4: tableNameが最大文字数（128文字）でも正常処理される"""
    payload = {**_BASE_PAYLOAD, "tableName": "a" * MAX_TABLE_NAME_LENGTH}
    response = client.post("/api/table/create-simulation-data", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_n5_table_name_exceeds_max_length(client, tables_store):
    """N5: tableNameが最大文字数を超えると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": "a" * (MAX_TABLE_NAME_LENGTH + 1)}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = (
        f"tableNameは{MAX_TABLE_NAME_LENGTH}文字以内で入力してください。"
    )
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_n6_table_name_with_tab(client, tables_store):
    """N6: tableNameにタブ文字が含まれると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": "Sim\tTable"}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == "tableNameに使用できない文字が含まれています。"
    )
    assert response_data["details"] == [
        "tableNameに使用できない文字が含まれています。"
    ]


def test_n7_table_name_only_spaces(client, tables_store):
    """N7: tableNameがスペースのみの場合、トリム後に空になり 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": "   "}
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]

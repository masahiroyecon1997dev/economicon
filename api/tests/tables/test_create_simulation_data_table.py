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
# 単独カラム設定（ガンマ分布）
_COL_GAMMA = {
    "columnName": "gamma_col",
    "distribution": {"type": "gamma", "shape": 2.0, "scale": 1.0},
}
# 単独カラム設定（ベータ分布）
_COL_BETA = {
    "columnName": "beta_col",
    "distribution": {"type": "beta", "a": 2.0, "b": 5.0},
}
# 単独カラム設定（ワイブル分布）
_COL_WEIBULL = {
    "columnName": "weibull_col",
    "distribution": {"type": "weibull", "a": 1.5, "scale": 1.0},
}
# 単独カラム設定（対数正規分布）
_COL_LOGNORMAL = {
    "columnName": "lognormal_col",
    "distribution": {"type": "lognormal", "mean": 0.0, "sigma": 1.0},
}
# 単独カラム設定（二項分布）
_COL_BINOMIAL = {
    "columnName": "binomial_col",
    "distribution": {"type": "binomial", "n": 10, "p": 0.5},
}
# 単独カラム設定（ベルヌーイ分布）
_COL_BERNOULLI = {
    "columnName": "bernoulli_col",
    "distribution": {"type": "bernoulli", "p": 0.5},
}
# 単独カラム設定（ポアソン分布）
_COL_POISSON = {
    "columnName": "poisson_col",
    "distribution": {"type": "poisson", "lam": 3.0},
}
# 単独カラム設定（幾何分布）
_COL_GEOMETRIC = {
    "columnName": "geometric_col",
    "distribution": {"type": "geometric", "p": 0.3},
}
# 単独カラム設定（超幾何分布）
_COL_HYPERGEOMETRIC = {
    "columnName": "hypergeometric_col",
    "distribution": {
        "type": "hypergeometric",
        "populationSize": 100,
        "successCount": 30,
        "sampleSize": 10,
    },
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
    expected_row_count = 100
    assert len(df) == expected_row_count
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
    expected_row_count = 50
    assert len(df) == expected_row_count
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
    expected_row_count = 30
    assert len(df) == expected_row_count


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
    expected_row_count = 10
    assert len(df) == expected_row_count
    assert "fixed_col" in df.columns
    # 全行が固定値 42.0 であることを確認
    fixed_value = 42.0
    assert (df["fixed_col"] == fixed_value).all()


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
    expected_row_count = 20
    assert len(df) == expected_row_count
    expected_column_count = 3
    assert len(df.columns) == expected_column_count
    assert "normal_col" in df.columns
    assert "uniform_col" in df.columns
    assert "exp_col" in df.columns


def test_create_table_with_all_distributions(client, tables_store):
    """全 13 分布タイプを含むテーブルを正常に作成できる"""
    all_cols = [
        _COL_NORMAL,
        _COL_UNIFORM,
        _COL_EXP,
        _COL_FIXED,
        _COL_GAMMA,
        _COL_BETA,
        _COL_WEIBULL,
        _COL_LOGNORMAL,
        _COL_BINOMIAL,
        _COL_BERNOULLI,
        _COL_POISSON,
        _COL_GEOMETRIC,
        _COL_HYPERGEOMETRIC,
    ]
    payload = {
        "tableName": "AllDistTable",
        "rowCount": 50,
        "simulationColumns": all_cols,
    }
    response = client.post("/api/table/create-simulation-data", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("AllDistTable").table
    expected_row_count = 50
    expected_col_count = len(all_cols)
    assert len(df) == expected_row_count
    assert len(df.columns) == expected_col_count

    # 各分布の値域を検証
    fixed_value = 42.0
    binomial_n = 10
    bernoulli_upper = 1
    hypergeometric_max = min(30, 10)  # min(successCount, sampleSize)
    assert (df["fixed_col"] == fixed_value).all()
    assert all(v >= 0 for v in df["gamma_col"])
    assert all(0 <= v <= 1 for v in df["beta_col"])
    assert all(v >= 0 for v in df["weibull_col"])
    assert all(v > 0 for v in df["lognormal_col"])
    assert all(0 <= v <= binomial_n for v in df["binomial_col"])
    assert all(v in (0, bernoulli_upper) for v in df["bernoulli_col"])
    assert all(v >= 0 for v in df["poisson_col"])
    assert all(v >= 1 for v in df["geometric_col"])
    assert all(0 <= v <= hypergeometric_max for v in df["hypergeometric_col"])


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
    """
    N7:
        tableNameがスペースのみの場合、トリム後に空になり 422 VALIDATION_ERROR
    """
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

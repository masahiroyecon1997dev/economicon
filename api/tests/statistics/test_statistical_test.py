"""統計的検定 API のテスト"""

from typing import Any

import numpy as np
import polars as pl
import pytest
import scipy.stats as spstats
from fastapi import status
from fastapi.testclient import TestClient
from statsmodels.stats.weightstats import ztest as sm_ztest

from economicon.services.data.tables_store import TablesStore
from main import app

# -----------------------------------------------------------
# 定数
# -----------------------------------------------------------

_TABLE_A = "StatTestTableA"
_TABLE_B = "StatTestTableB"
_TABLE_C = "StatTestTableC"
_TABLE_SMALL = "StatTestTableSmall"
_COL = "value"
_N = 50
_N_SMALL = 30
_SEED = 42

URL = "/api/statistics/test"

# -----------------------------------------------------------
# テストデータ（期待値計算用）
# -----------------------------------------------------------

rng = np.random.default_rng(_SEED)
_GROUP_A: np.ndarray = rng.normal(50, 10, _N)
_GROUP_B: np.ndarray = rng.normal(55, 10, _N)
_GROUP_C: np.ndarray = rng.normal(60, 10, _N)
_GROUP_SMALL: np.ndarray = rng.normal(50, 10, _N_SMALL)


# -----------------------------------------------------------
# フィクスチャ
# -----------------------------------------------------------


@pytest.fixture
def client():
    """TestClient のフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStore のフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()

    manager.store_table(_TABLE_A, pl.DataFrame({_COL: _GROUP_A}))
    manager.store_table(_TABLE_B, pl.DataFrame({_COL: _GROUP_B}))
    manager.store_table(_TABLE_C, pl.DataFrame({_COL: _GROUP_C}))
    manager.store_table(_TABLE_SMALL, pl.DataFrame({_COL: _GROUP_SMALL}))

    yield manager
    manager.clear_tables()


# -----------------------------------------------------------
# ヘルパー
# -----------------------------------------------------------


def _samples(
    *pairs: tuple[str, str],
) -> list[dict[str, str]]:
    """サンプルリストを生成するヘルパー"""
    return [{"tableName": t, "columnName": c} for t, c in pairs]


# -----------------------------------------------------------
# t-test 成功ケース
# -----------------------------------------------------------


def test_ttest_1sample_success(client, tables_store):
    """1 群 t 検定が正常に動作する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"alternative": "two-sided", "mu": 50.0},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert isinstance(result["statistic"], float)
    assert isinstance(result["pValue"], float)
    assert isinstance(result["df"], float)
    assert result["df"] == pytest.approx(_N - 1)
    assert result["confidenceInterval"] is not None
    assert (
        result["confidenceInterval"]["lower"]
        < (result["confidenceInterval"]["upper"])
    )
    assert result["effectSize"] is not None
    assert result["effectSize"] >= 0.0

    # scipy との値一致確認
    res: Any = spstats.ttest_1samp(_GROUP_A, popmean=50.0)
    assert result["statistic"] == pytest.approx(float(res.statistic), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(res.pvalue), rel=1e-5)


def test_ttest_2sample_independent_success(client, tables_store):
    """独立 2 群 t 検定（等分散）が正常に動作する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"equal_var": True},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert isinstance(result["statistic"], float)
    assert isinstance(result["pValue"], float)
    assert isinstance(result["df"], float)
    assert result["confidenceInterval"] is not None
    assert result["effectSize"] is not None

    res: Any = spstats.ttest_ind(_GROUP_A, _GROUP_B, equal_var=True)
    assert result["statistic"] == pytest.approx(float(res.statistic), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(res.pvalue), rel=1e-5)


def test_ttest_2sample_welch_success(client, tables_store):
    """独立 2 群 Welch t 検定（不等分散）が正常に動作する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"equalVar": False},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    res: Any = spstats.ttest_ind(_GROUP_A, _GROUP_B, equal_var=False)
    assert result["statistic"] == pytest.approx(float(res.statistic), rel=1e-5)


def test_ttest_paired_success(client, tables_store):
    """対応あり t 検定が正常に動作する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"paired": True},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert isinstance(result["statistic"], float)
    assert result["df"] == pytest.approx(_N - 1)
    assert result["confidenceInterval"] is not None
    assert result["effectSize"] is not None

    res: Any = spstats.ttest_rel(_GROUP_A, _GROUP_B)
    assert result["statistic"] == pytest.approx(float(res.statistic), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(res.pvalue), rel=1e-5)


def test_ttest_one_sided_success(client, tables_store):
    """片側 t 検定（larger）が正常に動作する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"alternative": "larger", "mu": 45.0},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    res: Any = spstats.ttest_1samp(
        _GROUP_A, popmean=45.0, alternative="greater"
    )
    result = response_data["result"]
    assert result["statistic"] == pytest.approx(float(res.statistic), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(res.pvalue), rel=1e-5)


# -----------------------------------------------------------
# z-test 成功ケース
# -----------------------------------------------------------


def test_ztest_1sample_success(client, tables_store):
    """1 群 z 検定が正常に動作する"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 50.0},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert isinstance(result["statistic"], float)
    assert isinstance(result["pValue"], float)
    assert result["df"] is None
    assert result["confidenceInterval"] is not None
    assert result["effectSize"] is None

    stat: Any
    p_val: Any
    stat, p_val = sm_ztest(
        _GROUP_A,
        value=50.0,  # type: ignore[arg-type]
        alternative="two-sided",  # type: ignore[arg-type]
    )
    assert result["statistic"] == pytest.approx(float(stat), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(p_val), rel=1e-5)


def test_ztest_2sample_success(client, tables_store):
    """2 群 z 検定が正常に動作する"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"alternative": "two-sided"},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["df"] is None

    stat: Any
    p_val: Any
    stat, p_val = sm_ztest(
        _GROUP_A,
        _GROUP_B,
        value=0.0,  # type: ignore[arg-type]
        alternative="two-sided",  # type: ignore[arg-type]
    )
    assert result["statistic"] == pytest.approx(float(stat), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(p_val), rel=1e-5)


# -----------------------------------------------------------
# f-test 成功ケース
# -----------------------------------------------------------


def test_ftest_variance_ratio_success(client, tables_store):
    """2 群の分散比 F 検定が正常に動作する"""
    payload = {
        "testType": "f-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert isinstance(result["statistic"], float)
    assert result["statistic"] > 0.0
    assert isinstance(result["pValue"], float)
    assert 0.0 <= result["pValue"] <= 1.0
    assert result["df"] == pytest.approx(_N - 1)  # df1 = n1-1
    assert result["df2"] == pytest.approx(_N - 1)  # df2 = n2-1
    assert result["confidenceInterval"] is None
    assert result["effectSize"] is None

    # 期待値確認
    f_stat = float(np.var(_GROUP_A, ddof=1) / np.var(_GROUP_B, ddof=1))
    assert result["statistic"] == pytest.approx(f_stat, rel=1e-5)


def test_ftest_anova_success(client, tables_store):
    """3 群 ANOVA が正常に動作する"""
    payload = {
        "testType": "f-test",
        "samples": _samples(
            (_TABLE_A, _COL),
            (_TABLE_B, _COL),
            (_TABLE_C, _COL),
        ),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert isinstance(result["statistic"], float)
    assert result["statistic"] > 0.0
    assert result["df"] == pytest.approx(2.0)  # df1 = k - 1 = 3 - 1
    assert result["df2"] == pytest.approx(3 * _N - 3)  # df2 = N - k = 150 - 3
    assert result["confidenceInterval"] is None
    assert result["effectSize"] is not None
    assert 0.0 <= result["effectSize"] <= 1.0

    res = spstats.f_oneway(_GROUP_A, _GROUP_B, _GROUP_C)
    assert result["statistic"] == pytest.approx(float(res.statistic), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(res.pvalue), rel=1e-5)


def test_ftest_options_not_required(client, tables_store):
    """f-test において options の省略が可能"""
    payload = {
        "testType": "f-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
    }
    response = client.post(URL, json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


# -----------------------------------------------------------
# バリデーションエラー（400）
# -----------------------------------------------------------


def test_invalid_table_name_validation(client, tables_store):
    """存在しないテーブル名を指定すると 400 が返る"""
    payload = {
        "testType": "t-test",
        "samples": _samples(("NonExistentTable", _COL)),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "DATA_NOT_FOUND"
    assert "NonExistentTable" in response_data["message"]


def test_invalid_column_name_validation(client, tables_store):
    """存在しない列名を指定すると 400 が返る"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, "no_such_column")),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "DATA_NOT_FOUND"
    assert "no_such_column" in response_data["message"]


def test_paired_unequal_size_validation(client, tables_store):
    """
    paired=True でサンプルサイズが異なる場合に
    400 が返る（TABLE_A: 50, TABLE_SMALL: 30）
    """
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_SMALL, _COL)),
        "options": {"paired": True},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "STATISTICAL_TEST_ERROR"
    assert "50" in response_data["message"]
    assert "30" in response_data["message"]


# -----------------------------------------------------------
# バリデーションエラー（422: Pydantic モデルバリデーション）
# -----------------------------------------------------------


def test_ftest_requires_at_least_2_samples(client, tables_store):
    """f-test に 1 サンプルのみ指定すると 422 が返る"""
    payload = {
        "testType": "f-test",
        "samples": _samples((_TABLE_A, _COL)),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"


def test_ttest_too_many_samples_validation(client, tables_store):
    """t-test に 3 サンプルを指定すると 422 が返る"""
    payload = {
        "testType": "t-test",
        "samples": _samples(
            (_TABLE_A, _COL),
            (_TABLE_B, _COL),
            (_TABLE_C, _COL),
        ),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"


def test_invalid_test_type_validation(client, tables_store):
    """無効な testType を指定すると 422 が返る"""
    payload = {
        "testType": "invalid-test",
        "samples": _samples((_TABLE_A, _COL)),
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_invalid_alternative_validation(client, tables_store):
    """無効な alternative を指定すると 422 が返る"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"alternative": "unknown"},
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# -----------------------------------------------------------
# レスポンスフィールドの存在確認
# -----------------------------------------------------------


def test_response_has_all_fields(client, tables_store):
    """
    レスポンスに statistic / pValue / df /
    confidenceInterval / effectSize が含まれる
    """
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 50.0},
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    for field in (
        "statistic",
        "pValue",
        "df",
        "df2",
        "confidenceInterval",
        "effectSize",
    ):
        assert field in result, f"レスポンスに '{field}' が存在しない"


def test_ztest_df_is_none(client, tables_store):
    """z 検定では df / df2 がともに None になる"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL)),
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]
    assert result["df"] is None
    assert result["df2"] is None


def test_ftest_variance_ratio_ci_is_none(client, tables_store):
    """分散比 F 検定では confidenceInterval が None になる"""
    payload = {
        "testType": "f-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
    }
    response = client.post(URL, json=payload)
    assert response.json()["result"]["confidenceInterval"] is None


def test_anova_effect_size_range(client, tables_store):
    """ANOVA の効果量（η²）が 0～1 の範囲に収まる"""
    payload = {
        "testType": "f-test",
        "samples": _samples(
            (_TABLE_A, _COL),
            (_TABLE_B, _COL),
            (_TABLE_C, _COL),
        ),
    }
    response = client.post(URL, json=payload)
    eta_sq = response.json()["result"]["effectSize"]

    assert eta_sq is not None
    assert 0.0 <= eta_sq <= 1.0

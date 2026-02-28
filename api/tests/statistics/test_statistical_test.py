"""統計的検定 API のテスト"""

from typing import Any
from unittest.mock import patch

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

# 追加テスト用テーブル名・列名
_TABLE_NULL_COL = "StatTestTableNullCol"
_TABLE_NARROW = "StatTestTableNarrow"
_TABLE_CONST = "StatTestTableConst"
_TABLE_JP = "統計テスト表"
_COL_JP = "測定値"

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
    _EXPECTED_MSG = (
        "Paired test requires equal sample sizes, but got 50 and 30"
    )
    assert response_data["message"] == _EXPECTED_MSG


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
    _EXPECTED_MSG = "f-test requires at least 2 samples, but got 1"
    assert response_data["message"] == _EXPECTED_MSG
    assert response_data["details"] == [_EXPECTED_MSG]


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
    _EXPECTED_MSG = "t-test supports up to 2 samples, but got 3"
    assert response_data["message"] == _EXPECTED_MSG
    assert response_data["details"] == [_EXPECTED_MSG]


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


# -----------------------------------------------------------
# C1 カバレッジ補完
# -----------------------------------------------------------


def test_all_null_column_validation(client, tables_store):
    """全 null カラムを渡すと 400 エラーが返り、メッセージ内容が完全一致する"""
    null_col = pl.Series([None] * _N, dtype=pl.Float64)
    tables_store.store_table(
        _TABLE_NULL_COL, pl.DataFrame({_COL: null_col})
    )
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_NULL_COL, _COL)),
        "options": {"mu": 50.0},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "STATISTICAL_TEST_ERROR"
    expected = "samples[0] contains no valid data (all values are null)"
    assert response_data["message"] == expected


def test_f_variance_ratio_f_less_than_1(client, tables_store):
    """
    分散比 F 検定: var_x < var_y のとき F < 1 となり
    p 値計算の cdf 側分岐を通る
    """
    # std≈1 の低分散グループ → var ≈1 << var(_GROUP_A) ≈1e2
    narrow = np.random.default_rng(99).normal(50, 1, _N)
    tables_store.store_table(
        _TABLE_NARROW, pl.DataFrame({_COL: narrow})
    )
    # narrow(var≈1) を x、A(var≈100) を y → F = var_narrow/var_A < 1
    payload = {
        "testType": "f-test",
        "samples": _samples((_TABLE_NARROW, _COL), (_TABLE_A, _COL)),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["statistic"] < 1.0  # F < 1 → cdf 側分岐の証明
    assert 0.0 < result["pValue"] < 1.0

    f_expected = float(
        np.var(narrow, ddof=1) / np.var(_GROUP_A, ddof=1)
    )
    assert result["statistic"] == pytest.approx(f_expected, rel=1e-5)


def test_anova_ss_total_zero(client, tables_store):
    """
    全群が同一定数のとき SS_total=0 → η² = 0.0 になる
    （_eta_squared の ss_total==0.0 ガード分岐を通る）
    """
    const_col = np.full(_N, 42.0)
    tables_store.store_table(
        _TABLE_CONST, pl.DataFrame({_COL: const_col})
    )
    payload = {
        "testType": "f-test",
        "samples": _samples(
            (_TABLE_CONST, _COL),
            (_TABLE_CONST, _COL),
            (_TABLE_CONST, _COL),
        ),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["effectSize"] == pytest.approx(0.0)


def test_ttest_one_sided_smaller(client, tables_store):
    """片側 t 検定（smaller: 左側）が正常に動作し、AlternativeHypothesis.SMALLER 変換分岐を通る"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"alternative": "smaller", "mu": 55.0},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    res: Any = spstats.ttest_1samp(
        _GROUP_A, popmean=55.0, alternative="less"
    )
    result = response_data["result"]
    assert result["statistic"] == pytest.approx(float(res.statistic), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(res.pvalue), rel=1e-5)


def test_unexpected_error_raises_500(client, tables_store):
    """
    サービス内部で予期しない例外発生時に 500 STATISTICAL_TEST_ERROR が返る
    （execute() の except Exception パスを通る）
    """
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 50.0},
    }
    with patch(
        "economicon.services.statistics.statistical_test"
        ".StatisticalTest._run_ttest",
        side_effect=RuntimeError("simulated internal error"),
    ):
        response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["code"] == "STATISTICAL_TEST_ERROR"


# -----------------------------------------------------------
# 意地悪なリクエスト (Robustness)
# -----------------------------------------------------------


def test_empty_samples_list_validation(client, tables_store):
    """samples が空リスト [] の場合、422 のメッセージ・ details が一致する"""
    payload = {
        "testType": "t-test",
        "samples": [],
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "VALIDATION_ERROR"
    expected_msg = "samplesは1件以上ある必要があります。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_japanese_table_name_success(client, tables_store):
    """日本語テーブル名で正常に存在確認・検定が動作する"""
    tables_store.store_table(_TABLE_JP, pl.DataFrame({_COL: _GROUP_A}))
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_JP, _COL)),
        "options": {"mu": 50.0},
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_japanese_column_name_success(client, tables_store):
    """日本語カラム名で正常に存在確認・検定が動作する"""
    tables_store.store_table(
        _TABLE_JP + "_col", pl.DataFrame({_COL_JP: _GROUP_A})
    )
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_JP + "_col", _COL_JP)),
        "options": {"mu": 50.0},
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_whitespace_trim_table_column_name(client, tables_store):
    """テーブル名・カラム名の前後スペースはトリムされ、正常に照合される"""
    payload = {
        "testType": "t-test",
        "samples": [
            {
                "tableName": f"  {_TABLE_A}  ",
                "columnName": f"  {_COL}  ",
            }
        ],
        "options": {"mu": 50.0},
    }
    response = client.post(URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "OK"


def test_ztest_one_sided_larger(client, tables_store):
    """z 検定: alternative="larger" が正常に動作する"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 45.0, "alternative": "larger"},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    stat: Any
    p_val: Any
    stat, p_val = sm_ztest(
        _GROUP_A,
        value=45.0,  # type: ignore[arg-type]
        alternative="larger",  # type: ignore[arg-type]
    )
    result = response_data["result"]
    assert result["statistic"] == pytest.approx(float(stat), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(p_val), rel=1e-5)


def test_ztest_one_sided_smaller(client, tables_store):
    """z 検定: alternative="smaller" が正常に動作する"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 55.0, "alternative": "smaller"},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    stat: Any
    p_val: Any
    stat, p_val = sm_ztest(
        _GROUP_A,
        value=55.0,  # type: ignore[arg-type]
        alternative="smaller",  # type: ignore[arg-type]
    )
    result = response_data["result"]
    assert result["statistic"] == pytest.approx(float(stat), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(p_val), rel=1e-5)


# -----------------------------------------------------------
# 統計的境界値
# -----------------------------------------------------------


def test_ttest_1sample_mu_default(client, tables_store):
    """mu を省略すると 0.0 がデフォルト値として使用される"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    res: Any = spstats.ttest_1samp(_GROUP_A, popmean=0.0)
    result = response_data["result"]
    assert result["statistic"] == pytest.approx(float(res.statistic), rel=1e-5)
    assert result["pValue"] == pytest.approx(float(res.pvalue), rel=1e-5)


def test_ttest_2sample_ci_bounds(client, tables_store):
    """
    独立 2 群・Welch・対応あり t 検定の
    信頼区間が lower < upper を満たす
    """
    cases = [
        # 等分散
        {
            "testType": "t-test",
            "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
            "options": {"equalVar": True},
        },
        # Welch
        {
            "testType": "t-test",
            "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
            "options": {"equalVar": False},
        },
        # 対応あり
        {
            "testType": "t-test",
            "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
            "options": {"paired": True},
        },
    ]
    for payload in cases:
        result = client.post(URL, json=payload).json()["result"]
        ci = result["confidenceInterval"]
        assert ci is not None, f"CI が None: {payload['options']}"
        assert ci["lower"] < ci["upper"], (
            f"lower >= upper: {ci}, options={payload['options']}"
        )


# -----------------------------------------------------------
# 冪等性
# -----------------------------------------------------------


def test_idempotency(client, tables_store):
    """同一リクエストの連続実行で statistic / pValue / df / effectSize が完全一致する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"equalVar": True},
    }
    r1 = client.post(URL, json=payload).json()
    r2 = client.post(URL, json=payload).json()

    assert r1["code"] == r2["code"] == "OK"
    assert r1["result"]["statistic"] == r2["result"]["statistic"]
    assert r1["result"]["pValue"] == r2["result"]["pValue"]
    assert r1["result"]["df"] == r2["result"]["df"]
    assert r1["result"]["effectSize"] == r2["result"]["effectSize"]

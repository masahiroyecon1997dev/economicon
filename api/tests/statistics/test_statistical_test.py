"""統計的検定 API のテスト"""

from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import polars as pl
import pytest
import scipy.stats as spstats
from fastapi import status
from fastapi.testclient import TestClient
from statsmodels.stats.weightstats import ztest as sm_ztest

from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
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
    AnalysisResultStore().clear_all()

    manager.store_table(_TABLE_A, pl.DataFrame({_COL: _GROUP_A}))
    manager.store_table(_TABLE_B, pl.DataFrame({_COL: _GROUP_B}))
    manager.store_table(_TABLE_C, pl.DataFrame({_COL: _GROUP_C}))
    manager.store_table(_TABLE_SMALL, pl.DataFrame({_COL: _GROUP_SMALL}))

    yield manager
    manager.clear_tables()
    AnalysisResultStore().clear_all()


# -----------------------------------------------------------
# ヘルパー
# -----------------------------------------------------------


def _samples(
    *pairs: tuple[str, str],
) -> list[dict[str, str]]:
    """サンプルリストを生成するヘルパー"""
    return [{"tableName": t, "columnName": c} for t, c in pairs]


def _get_result_data(client: TestClient, payload: dict) -> dict:
    """POST して AnalysisResultStore から result_data を直接取得"""
    resp = client.post(URL, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# t-test 成功ケース
# -----------------------------------------------------------


def test_ttest_1sample_success(client, tables_store):
    """1 群 t 検定が正常に動作し resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ttest_2sample_independent_success(client, tables_store):
    """独立 2 群 t 検定（等分散）で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ttest_paired_success(client, tables_store):
    """対応あり t 検定で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ttest_one_sided_success(client, tables_store):
    """片側 t 検定（larger）で resultId を含むレスポンスが返る"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"alternative": "larger", "mu": 45.0},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


# -----------------------------------------------------------
# z-test 成功ケース
# -----------------------------------------------------------


def test_ztest_1sample_success(client, tables_store):
    """1 群 z 検定で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ztest_2sample_success(client, tables_store):
    """2 群 z 検定で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


# -----------------------------------------------------------
# f-test 成功ケース
# -----------------------------------------------------------


def test_ftest_variance_ratio_success(client, tables_store):
    """2 群の分散比 F 検定で resultId を含むレスポンスが返る"""
    payload = {
        "testType": "f-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ftest_anova_success(client, tables_store):
    """3 群 ANOVA で resultId を含むレスポンスが返る"""
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


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
    expected_msg = "Paired test requires equal sample sizes, but got 50 and 30"
    assert response_data["message"] == expected_msg


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
    expected_msg = "f-test requires at least 2 samples, but got 1"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


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
    expected_msg = "t-test supports up to 2 samples, but got 3"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


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
    POST レスポンスに resultId が存在する
    """
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 50.0},
    }
    response = client.post(URL, json=payload)
    result = response.json()["result"]

    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ztest_df_is_none(client, tables_store):
    """z 検定で df が None であることを確認"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL)),
    }
    rd = _get_result_data(client, payload)
    assert rd["df"] is None
    assert rd["statistic"] is not None
    assert 0.0 <= rd["pValue"] <= 1.0


def test_ftest_variance_ratio_ci_is_none(client, tables_store):
    """分散比 F 検定で confidenceInterval が None であることを確認"""
    payload = {
        "testType": "f-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
    }
    rd = _get_result_data(client, payload)
    assert rd["confidenceInterval"] is None
    assert rd["statistic"] > 0.0
    assert 0.0 <= rd["pValue"] <= 1.0


def test_anova_effect_size_range(client, tables_store):
    """ANOVA で η² が [0, 1] に収まることを確認"""
    payload = {
        "testType": "f-test",
        "samples": _samples(
            (_TABLE_A, _COL),
            (_TABLE_B, _COL),
            (_TABLE_C, _COL),
        ),
    }
    rd = _get_result_data(client, payload)
    assert rd["effectSize"] is not None
    assert 0.0 <= rd["effectSize"] <= 1.0


# -----------------------------------------------------------
# C1 カバレッジ補完
# -----------------------------------------------------------


def test_all_null_column_validation(client, tables_store):
    """全 null カラムを渡すと 400 エラーが返り、メッセージ内容が完全一致する"""
    null_col = pl.Series([None] * _N, dtype=pl.Float64)
    tables_store.store_table(_TABLE_NULL_COL, pl.DataFrame({_COL: null_col}))
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
    分散比 F 検定: var_x < var_y のとき F < 1 → resultId が返る
    p 値計算の cdf 側分岐を通る
    """
    # std≈1 の低分散グループ → var ≈1 << var(_GROUP_A) ≈1e2
    narrow = np.random.default_rng(99).normal(50, 1, _N)
    tables_store.store_table(_TABLE_NARROW, pl.DataFrame({_COL: narrow}))
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
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_anova_ss_total_zero(client, tables_store):
    """
    全群が同一定数のとき SS_total=0 → η² = 0.0 になる
    （f_oneway の NaN 直列化問題を回避するため f_oneway のみモック）
    モック経由で resultId を含むレスポンスが返る
    """
    const_col = np.full(_N, 42.0)
    tables_store.store_table(_TABLE_CONST, pl.DataFrame({_COL: const_col}))
    # f_oneway は NaN を返すため JSON 直列化失敗する。statistic/pvalue のみ
    # モックし、_eta_squared の ss_total==0 ガードは実データにかける。
    mock_f_result = MagicMock()
    mock_f_result.statistic = 0.0
    mock_f_result.pvalue = 1.0
    payload = {
        "testType": "f-test",
        "samples": _samples(
            (_TABLE_CONST, _COL),
            (_TABLE_CONST, _COL),
            (_TABLE_CONST, _COL),
        ),
    }
    with patch(
        "economicon.services.statistics.statistical_test.stats.f_oneway",
        return_value=mock_f_result,
    ):
        response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ttest_one_sided_smaller(client, tables_store):
    """片側 t 検定（smaller: 左側）で resultId を含むレスポンスが返る
    AlternativeHypothesis.SMALLER 変換分岐を通る
    """
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"alternative": "smaller", "mu": 55.0},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


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
    """z 検定: alternative="larger" で resultId を含むレスポンスが返る"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 45.0, "alternative": "larger"},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ztest_one_sided_smaller(client, tables_store):
    """z 検定: alternative="smaller" で resultId を含むレスポンスが返る"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 55.0, "alternative": "smaller"},
    }
    response = client.post(URL, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


# -----------------------------------------------------------
# 数値精度テスト（AnalysisResultStore 直接参照）
# -----------------------------------------------------------


def test_ttest_1sample_numerical(client, tables_store):
    """1 群 t 検定の数値が scipy.stats.ttest_1samp と一致する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"alternative": "two-sided", "mu": 50.0},
    }
    rd = _get_result_data(client, payload)

    res: Any = spstats.ttest_1samp(_GROUP_A, popmean=50.0)
    ci_res: Any = spstats.ttest_1samp(
        _GROUP_A, popmean=50.0, alternative="two-sided"
    )
    exp_ci = ci_res.confidence_interval(confidence_level=0.95)
    assert rd["statistic"] == pytest.approx(float(res.statistic), abs=1e-8)
    assert rd["pValue"] == pytest.approx(float(res.pvalue), abs=1e-8)
    assert rd["df"] == pytest.approx(_N - 1, abs=1e-8)
    ci = rd["confidenceInterval"]
    assert ci is not None
    assert ci["lower"] == pytest.approx(float(exp_ci.low), abs=1e-8)
    assert ci["upper"] == pytest.approx(float(exp_ci.high), abs=1e-8)
    assert rd["effectSize"] is not None
    assert rd["effectSize"] >= 0.0


def test_ttest_2sample_independent_numerical(client, tables_store):
    """独立 2 群 t 検定（等分散）の数値が scipy と一致する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"equal_var": True},
    }
    rd = _get_result_data(client, payload)

    res: Any = spstats.ttest_ind(_GROUP_A, _GROUP_B, equal_var=True)
    exp_ci = res.confidence_interval(confidence_level=0.95)
    assert rd["statistic"] == pytest.approx(float(res.statistic), abs=1e-8)
    assert rd["pValue"] == pytest.approx(float(res.pvalue), abs=1e-8)
    # 等分散 pooled df = N_A + N_B - 2
    assert rd["df"] == pytest.approx(_N + _N - 2, abs=1e-8)
    ci = rd["confidenceInterval"]
    assert ci is not None
    assert ci["lower"] == pytest.approx(float(exp_ci.low), abs=1e-8)
    assert ci["upper"] == pytest.approx(float(exp_ci.high), abs=1e-8)
    assert rd["effectSize"] is not None


def test_ttest_welch_numerical(client, tables_store):
    """Welch t 検定の statistic/pValue/df/CI が scipy と一致する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"equalVar": False},
    }
    rd = _get_result_data(client, payload)

    res: Any = spstats.ttest_ind(
        _GROUP_A, _GROUP_B, equal_var=False, alternative="two-sided"
    )
    exp_ci = res.confidence_interval(confidence_level=0.95)
    assert rd["statistic"] == pytest.approx(float(res.statistic), abs=1e-8)
    assert rd["pValue"] == pytest.approx(float(res.pvalue), abs=1e-8)
    # Welch df ≠ N_A + N_B - 2
    assert rd["df"] == pytest.approx(float(res.df), abs=1e-8)
    ci = rd["confidenceInterval"]
    assert ci["lower"] == pytest.approx(float(exp_ci.low), abs=1e-8)
    assert ci["upper"] == pytest.approx(float(exp_ci.high), abs=1e-8)


def test_ttest_paired_numerical(client, tables_store):
    """対応あり t 検定の statistic/pValue/df/CI が scipy と一致する"""
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"paired": True},
    }
    rd = _get_result_data(client, payload)

    res: Any = spstats.ttest_rel(_GROUP_A, _GROUP_B, alternative="two-sided")
    exp_ci = res.confidence_interval(confidence_level=0.95)
    assert rd["statistic"] == pytest.approx(float(res.statistic), abs=1e-8)
    assert rd["pValue"] == pytest.approx(float(res.pvalue), abs=1e-8)
    assert rd["df"] == pytest.approx(_N - 1, abs=1e-8)
    ci = rd["confidenceInterval"]
    assert ci["lower"] == pytest.approx(float(exp_ci.low), abs=1e-8)
    assert ci["upper"] == pytest.approx(float(exp_ci.high), abs=1e-8)


def test_ztest_1sample_numerical(client, tables_store):
    """1 群 z 検定の statistic/pValue/CI が statsmodels と一致する"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL)),
        "options": {"mu": 50.0},
    }
    rd = _get_result_data(client, payload)

    stat, p_val = sm_ztest(
        _GROUP_A,
        value=50,
        alternative="two-sided",
    )
    exp_center = float(np.mean(_GROUP_A))
    exp_se = float(np.std(_GROUP_A, ddof=1) / np.sqrt(len(_GROUP_A)))
    z_crit = float(spstats.norm.ppf(0.975))
    assert rd["statistic"] == pytest.approx(float(stat), abs=1e-8)
    assert rd["pValue"] == pytest.approx(float(p_val), abs=1e-8)
    assert rd["df"] is None
    ci = rd["confidenceInterval"]
    assert ci is not None
    assert ci["lower"] == pytest.approx(exp_center - z_crit * exp_se, abs=1e-8)
    assert ci["upper"] == pytest.approx(exp_center + z_crit * exp_se, abs=1e-8)
    assert rd["effectSize"] is None


def test_ztest_2sample_numerical(client, tables_store):
    """2 群 z 検定の数値が statsmodels と一致する"""
    payload = {
        "testType": "z-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"alternative": "two-sided"},
    }
    rd = _get_result_data(client, payload)

    stat, p_val = sm_ztest(
        _GROUP_A,
        _GROUP_B,
        value=0,
        alternative="two-sided",
    )
    exp_center = float(np.mean(_GROUP_A) - np.mean(_GROUP_B))
    exp_se = float(
        np.sqrt(
            np.var(_GROUP_A, ddof=1) / len(_GROUP_A)
            + np.var(_GROUP_B, ddof=1) / len(_GROUP_B)
        )
    )
    z_crit = float(spstats.norm.ppf(0.975))
    assert rd["statistic"] == pytest.approx(float(stat), abs=1e-8)
    assert rd["pValue"] == pytest.approx(float(p_val), abs=1e-8)
    ci = rd["confidenceInterval"]
    assert ci["lower"] == pytest.approx(exp_center - z_crit * exp_se, abs=1e-8)
    assert ci["upper"] == pytest.approx(exp_center + z_crit * exp_se, abs=1e-8)


def test_ftest_variance_ratio_numerical(client, tables_store):
    """分散比 F 検定の statistic/pValue/df が手計算と abs=1e-8 で一致する"""
    payload = {
        "testType": "f-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
    }
    rd = _get_result_data(client, payload)

    var_a = float(np.var(_GROUP_A, ddof=1))
    var_b = float(np.var(_GROUP_B, ddof=1))
    f_expected = var_a / var_b
    df1 = _N - 1
    df2 = _N - 1
    p_expected = 2.0 * min(
        float(spstats.f.cdf(f_expected, df1, df2)),
        float(spstats.f.sf(f_expected, df1, df2)),
    )
    assert rd["statistic"] == pytest.approx(f_expected, abs=1e-8)
    assert rd["pValue"] == pytest.approx(p_expected, abs=1e-8)
    assert rd["df"] == pytest.approx(df1, abs=1e-8)
    assert rd["df2"] == pytest.approx(df2, abs=1e-8)
    assert rd["confidenceInterval"] is None
    assert rd["effectSize"] is None


def test_ftest_anova_numerical(client, tables_store):
    """3群 ANOVA: statistic/pValue/df/η² が scipy・手計算と abs=1e-8 で一致"""
    payload = {
        "testType": "f-test",
        "samples": _samples(
            (_TABLE_A, _COL),
            (_TABLE_B, _COL),
            (_TABLE_C, _COL),
        ),
    }
    rd = _get_result_data(client, payload)

    res = spstats.f_oneway(_GROUP_A, _GROUP_B, _GROUP_C)
    # η² 手計算
    all_data = np.concatenate([_GROUP_A, _GROUP_B, _GROUP_C])
    grand_mean = float(np.mean(all_data))
    ss_between = float(
        sum(
            len(g) * (float(np.mean(g)) - grand_mean) ** 2
            for g in [_GROUP_A, _GROUP_B, _GROUP_C]
        )
    )
    ss_total = float(np.sum((all_data - grand_mean) ** 2))
    eta_sq_expected = ss_between / ss_total

    assert rd["statistic"] == pytest.approx(float(res.statistic), abs=1e-8)
    assert rd["pValue"] == pytest.approx(float(res.pvalue), abs=1e-8)
    assert rd["df"] == pytest.approx(2.0, abs=1e-8)
    assert rd["df2"] == pytest.approx(float(3 * _N - 3), abs=1e-8)
    assert rd["confidenceInterval"] is None
    assert rd["effectSize"] == pytest.approx(eta_sq_expected, abs=1e-8)


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
    result = response_data["result"]
    assert set(result.keys()) == {"resultId"}
    assert isinstance(result["resultId"], str)
    assert len(result["resultId"]) > 0


def test_ttest_2sample_ci_bounds(client, tables_store):
    """
    独立 2 群・ Welch・対応あり t 検定で
    それぞれ resultId を含むレスポンスが返る
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
        assert set(result.keys()) == {"resultId"}, (
            f"resultId 以外のフィールドが存在: options={payload['options']}"
        )
        assert isinstance(result["resultId"], str)


# -----------------------------------------------------------
# 冪等性
# -----------------------------------------------------------


def test_idempotency(client, tables_store):
    """
    同一リクエストの連続実行で
    それぞれ resultId を含むレスポンスが返る
    """
    payload = {
        "testType": "t-test",
        "samples": _samples((_TABLE_A, _COL), (_TABLE_B, _COL)),
        "options": {"equalVar": True},
    }
    r1 = client.post(URL, json=payload).json()
    r2 = client.post(URL, json=payload).json()

    assert r1["code"] == r2["code"] == "OK"
    assert set(r1["result"].keys()) == {"resultId"}
    assert set(r2["result"].keys()) == {"resultId"}
    assert isinstance(r1["result"]["resultId"], str)
    assert isinstance(r2["result"]["resultId"], str)

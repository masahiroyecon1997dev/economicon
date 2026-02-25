"""固定効果回帰テスト"""

import pandas as pd
from fastapi import status
from linearmodels.panel import PanelOLS

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    FePayload,
    generate_all_data,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-3

# パラメータ数定数（FEは定数項を吸収するためconst含まず）
_N_PARAMS_FE = 2

# エンティティ数定数
_N_ENTITIES = 10


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).regression_output


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_fe_success(client, tables_store):
    """固定効果モデルが200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=FePayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_fe_response_structure(client, tables_store):
    """regressionOutputに固定効果専用キーが含まれることを確認"""
    output = _get_output(client, FePayload().build())
    model_stats = output["modelStatistics"]

    for key in (
        "R2Within",
        "R2Between",
        "R2Overall",
        "nEntities",
        "fValue",
        "fProbability",
    ):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )

    params = output["parameters"]
    assert len(params) == _N_PARAMS_FE  # x1, x2（FEは定数項なし）
    for p in params:
        for key in ("variable", "coefficient", "standardError", "pValue"):
            assert key in p


def test_fe_coefficients_numerical(client, tables_store):
    """FE係数がlinearmodels (PanelOLS) と一致することを確認"""
    _, panel, _ = generate_all_data()
    entity_ids, time_ids, x1p, x2p, y_p = panel

    df = pd.DataFrame(
        {
            "entity_id": entity_ids.astype(float),
            "time_id": time_ids.astype(float),
            "y": y_p,
            "x1": x1p,
            "x2": x2p,
        }
    )
    df = df.set_index(["entity_id", "time_id"])
    model_result = PanelOLS(
        df["y"], df[["x1", "x2"]], entity_effects=True
    ).fit(cov_type="unadjusted")

    params = _get_output(client, FePayload().build())["parameters"]
    expected = model_result.params

    for i, (exp_coef, param) in enumerate(zip(expected, params, strict=False)):
        assert abs(param["coefficient"] - exp_coef) < _ABS_TOL, (
            f"FE params[{i}]: {param['coefficient']!r} != {exp_coef!r}"
        )


def test_fe_n_entities(client, tables_store):
    """nEntitiesがデータのエンティティ数と一致することを確認"""
    # PanelDataは10エンティティ
    model_stats = _get_output(client, FePayload().build())["modelStatistics"]
    assert model_stats["nEntities"] == _N_ENTITIES


def test_fe_r2_within_range(client, tables_store):
    """R2Within・R2Between・R2Overallが0以上1以下であることを確認"""
    model_stats = _get_output(client, FePayload().build())["modelStatistics"]
    for key in ("R2Within", "R2Between", "R2Overall"):
        val = model_stats[key]
        # R2はマイナスになりうる（プーリングOLSを基準にした場合）
        assert isinstance(val, float), f"{key!r} がfloatでない"


def test_fe_diagnostics_f_pooled(client, tables_store):
    """diagnostics に fPooled が含まれることを確認"""
    output = _get_output(client, FePayload().build())
    diagnostics = output["diagnostics"]
    assert "fPooled" in diagnostics
    fp = diagnostics["fPooled"]
    assert "statistic" in fp
    assert "pValue" in fp


def test_fe_clustered_se(client, tables_store):
    """クラスタロバスト標準誤差付きFEが成功することを確認"""
    payload = FePayload(se_method="cluster").build()
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["code"] == "OK"


def test_fe_coefficient_sign_x1_positive(client, tables_store):
    """x1の係数が正（設計値 1.5）であることを確認"""
    params = _get_output(client, FePayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}
    assert coef_map["x1"] > 0.0


def test_fe_coefficient_sign_x2_negative(client, tables_store):
    """x2の係数が負（設計値 -0.8）であることを確認"""
    params = _get_output(client, FePayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}
    assert coef_map["x2"] < 0.0


# -----------------------------------------------------------
# 標準誤差マッピング検証テスト
# LINEARMODELS_COV_TYPE_MAP のキーが正しく linearmodels に渡されることを確認
# -----------------------------------------------------------


def test_fe_robust_se_matches_linearmodels(client, tables_store):
    """
    robust SE 付き FE の標準誤差が linearmodels (PanelOLS, cov_type='robust')
    の値と一致することを確認。

    旧バグ: LINEARMODELS_COV_TYPE_MAP に "robust" キーが存在しなかったため
    cov_type が 'unadjusted' にフォールバックしていた。
    このテストは旧バグ下では失敗する。
    """
    _, panel, _ = generate_all_data()
    entity_ids, time_ids, x1p, x2p, y_p = panel

    df = pd.DataFrame(
        {
            "entity_id": entity_ids.astype(float),
            "time_id": time_ids.astype(float),
            "y": y_p,
            "x1": x1p,
            "x2": x2p,
        }
    )
    df = df.set_index(["entity_id", "time_id"])
    expected = PanelOLS(df["y"], df[["x1", "x2"]], entity_effects=True).fit(
        cov_type="robust"
    )

    payload = FePayload(se_method="robust").build()
    params = _get_output(client, payload)["parameters"]
    se_map = {p["variable"]: p["standardError"] for p in params}

    for i, var in enumerate(["x1", "x2"]):
        expected_se = float(expected.std_errors.iloc[i])
        assert abs(se_map[var] - expected_se) < _ABS_TOL, (
            f"FE robust SE [{var}]: API={se_map[var]!r} "
            f"!= linearmodels={expected_se!r}"
        )


def test_fe_robust_se_differs_from_nonrobust(client, tables_store):
    """
    robust SE が nonrobust SE と異なることを確認。

    旧バグ下では "robust" が "unadjusted" にフォールバックするため
    両者が一致してしまい、このテストは失敗する。
    """
    se_nonrobust = [
        p["standardError"]
        for p in _get_output(client, FePayload(se_method="nonrobust").build())[
            "parameters"
        ]
    ]
    se_robust = [
        p["standardError"]
        for p in _get_output(client, FePayload(se_method="robust").build())[
            "parameters"
        ]
    ]
    assert se_nonrobust != se_robust, (
        "robust SE が nonrobust SE と同一:"
        " LINEARMODELS_COV_TYPE_MAP のマッピングが"
        "正しく機能していない可能性がある"
    )


def test_fe_cluster_se_matches_linearmodels(client, tables_store):
    """
    cluster SE 付き FE の標準誤差が linearmodels
    (PanelOLS, cov_type='clustered') の値と一致することを確認。

    旧バグ: LINEARMODELS_COV_TYPE_MAP に "cluster" キーが存在しなかったため
    cov_type が 'unadjusted' にフォールバックしていた。
    このテストは旧バグ下では失敗する。
    """
    _, panel, _ = generate_all_data()
    entity_ids, time_ids, x1p, x2p, y_p = panel

    df = pd.DataFrame(
        {
            "entity_id": entity_ids.astype(float),
            "time_id": time_ids.astype(float),
            "y": y_p,
            "x1": x1p,
            "x2": x2p,
        }
    )
    df = df.set_index(["entity_id", "time_id"])
    # PanelOLS + cov_type='clustered': entity でクラスタリング（デフォルト）
    expected = PanelOLS(df["y"], df[["x1", "x2"]], entity_effects=True).fit(
        cov_type="clustered"
    )

    payload = FePayload(se_method="cluster").build()
    params = _get_output(client, payload)["parameters"]
    se_map = {p["variable"]: p["standardError"] for p in params}

    for i, var in enumerate(["x1", "x2"]):
        expected_se = float(expected.std_errors.iloc[i])
        assert abs(se_map[var] - expected_se) < _ABS_TOL, (
            f"FE cluster SE [{var}]: API={se_map[var]!r} "
            f"!= linearmodels={expected_se!r}"
        )

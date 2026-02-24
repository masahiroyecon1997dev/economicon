"""変量効果回帰テスト"""

import pandas as pd
from fastapi import status
from linearmodels.panel import RandomEffects

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    generate_all_data,
    re_payload,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-3

# nObservations 定数（10 エンティティ × 5 期間 = 50）
_N_OBS = 50


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).regression_output


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_re_success(client, tables_store):
    """変量効果モデルが200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=re_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_re_response_structure(client, tables_store):
    """regressionOutputに変量効果専用キーが含まれることを確認"""
    output = _get_output(client, re_payload())
    model_stats = output["modelStatistics"]

    for key in ("R2Within", "R2Between", "R2Overall"):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )

    params = output["parameters"]
    assert len(params) > 0
    for p in params:
        for key in ("variable", "coefficient", "standardError", "pValue"):
            assert key in p


def test_re_coefficients_numerical(client, tables_store):
    """RE係数がlinearmodels (RandomEffects) と一致することを確認"""
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
    model_result = RandomEffects(df["y"], df[["x1", "x2"]]).fit(
        cov_type="unadjusted"
    )

    params = _get_output(client, re_payload())["parameters"]
    expected = model_result.params  # pandas Series

    for i, (exp_coef, param) in enumerate(zip(expected, params, strict=False)):
        assert abs(param["coefficient"] - exp_coef) < _ABS_TOL, (
            f"RE params[{i}]: {param['coefficient']!r} != {exp_coef!r}"
        )


def test_re_theta_range(client, tables_store):
    """diagnostics の theta が 0 以上 1 以下であることを確認"""
    output = _get_output(client, re_payload())
    diagnostics = output["diagnostics"]

    if "theta" in diagnostics:
        theta = diagnostics["theta"]
        assert 0.0 <= theta <= 1.0, f"theta={theta!r} が範囲外"


def test_re_r2_values_are_float(client, tables_store):
    """R2Within・R2Between・R2Overallが数値であることを確認"""
    model_stats = _get_output(client, re_payload())["modelStatistics"]
    for key in ("R2Within", "R2Between", "R2Overall"):
        assert isinstance(model_stats[key], float), f"{key!r} がfloatでない"


def test_re_n_observations(client, tables_store):
    """nObservationsがPanelDataの行数と一致することを確認"""
    model_stats = _get_output(client, re_payload())["modelStatistics"]
    assert model_stats["nObservations"] == _N_OBS


def test_re_coefficient_sign_x1_positive(client, tables_store):
    """x1の係数が正（設計値 1.5）であることを確認"""
    params = _get_output(client, re_payload())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}
    assert coef_map["x1"] > 0.0


def test_re_coefficient_sign_x2_negative(client, tables_store):
    """x2の係数が負（設計値 -0.8）であることを確認"""
    params = _get_output(client, re_payload())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}
    assert coef_map["x2"] < 0.0

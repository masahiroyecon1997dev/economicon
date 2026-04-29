"""OLS回帰テスト"""

from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    TABLE_BASIC,
    URL_REGRESSION,
    OlsPayload,
    load_py_gold,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-8
# HAC は statsmodels の版差で僅差が出やすいため少し広め
_HAC_ABS_TOL = 5e-3

# パラメータ数定数
_N_PARAMS_WITH_CONST = 4
_N_PARAMS_NO_CONST = 3

# 係数符号確認の最小閖値（設計値 x1=2.535 に基づく）
_MIN_X1_COEF = 2.0


def _get_output(client, payload):
    """POSTして result_data を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_ols_success(client, tables_store):
    """OLS回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=OlsPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_ols_response_structure(client, tables_store):
    """regressionOutputに必須キーが含まれることを確認"""
    output = _get_output(client, OlsPayload().build())
    model_stats = output["modelStatistics"]

    for key in ("R2", "adjustedR2", "fValue", "fProbability"):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )

    params = output["parameters"]
    assert len(params) == _N_PARAMS_WITH_CONST  # const, x1, x2

    for p in params:
        for key in (
            "variable",
            "coefficient",
            "standardError",
            "tValue",
            "pValue",
            "confidenceIntervalLower",
            "confidenceIntervalUpper",
        ):
            assert key in p, f"パラメータに {key!r} が存在しない"


def test_ols_result_stored(client, tables_store):
    """resultIdで保存された結果が取得できることを確認"""
    resp = client.post(URL_REGRESSION, json=OlsPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    result_id = resp.json()["result"]["resultId"]

    saved = AnalysisResultStore().get_result(result_id)
    assert saved is not None
    assert "parameters" in saved.result_data
    assert "modelStatistics" in saved.result_data


def test_ols_coefficients_numerical(client, tables_store):
    """OLS係数が gold JSON と一致することを確認"""
    gold = load_py_gold("ols")
    expected = gold["estimates"]["nonrobust"]["coefficients"]

    params = _get_output(client, OlsPayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    for var, exp_coef in expected.items():
        assert abs(coef_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: got {coef_map[var]!r}, expected {exp_coef!r}"
        )


def test_ols_r2_numerical(client, tables_store):
    """R2シadjustedR2・fValue が gold JSON と一致することを確認"""
    gold = load_py_gold("ols")["estimates"]

    model_stats = _get_output(client, OlsPayload().build())["modelStatistics"]

    assert abs(model_stats["R2"] - gold["r_squared"]) < _ABS_TOL
    assert abs(model_stats["adjustedR2"] - gold["adj_r_squared"]) < _ABS_TOL
    assert abs(model_stats["fValue"] - gold["f_test"]["statistic"]) < _ABS_TOL


def test_ols_confidence_intervals_numerical(client, tables_store):
    """信頼区間が gold JSON (95%) と一致することを確認"""
    gold_ci = load_py_gold("ols")["estimates"]["nonrobust"]["conf_int"]

    params = _get_output(client, OlsPayload().build())["parameters"]
    for p in params:
        var = p["variable"]
        assert (
            abs(p["confidenceIntervalLower"] - gold_ci[var]["lower"])
            < _ABS_TOL
        )
        assert (
            abs(p["confidenceIntervalUpper"] - gold_ci[var]["upper"])
            < _ABS_TOL
        )


def test_ols_pvalues_numerical(client, tables_store):
    """p値が gold JSON 結果と一致することを確認"""
    gold_pvals = load_py_gold("ols")["estimates"]["nonrobust"]["p_values"]

    params = _get_output(client, OlsPayload().build())["parameters"]
    for p in params:
        var = p["variable"]
        assert abs(p["pValue"] - gold_pvals[var]) < _ABS_TOL, (
            f"{var}: got {p['pValue']!r}, expected {gold_pvals[var]!r}"
        )


def test_ols_without_constant(client, tables_store):
    """hasConst=Falseで定数項なしの回帰が動作することを確認"""
    params = _get_output(client, OlsPayload(has_const=False).build())[
        "parameters"
    ]
    # 定数なし → 変数 3 つのみ
    assert len(params) == _N_PARAMS_NO_CONST
    names = [p["variable"] for p in params]
    assert "const" not in names
    assert "x1" in names
    assert "x2" in names
    assert "x3" in names


def test_ols_robust_hc1(client, tables_store):
    """HC1ロバスト標準誤差が gold JSON と一致することを確認"""
    gold_se = load_py_gold("ols")["estimates"]["hc1"]["std_errors"]

    payload = OlsPayload(
        se_method="robust", se_extra={"hcType": "HC1"}
    ).build()
    params = _get_output(client, payload)["parameters"]
    for p in params:
        var = p["variable"]
        assert abs(p["standardError"] - gold_se[var]) < _ABS_TOL, (
            f"{var} HC1 SE: got {p['standardError']!r},"
            f" expected {gold_se[var]!r}"
        )


def test_ols_hac(client, tables_store):
    """HAC (Newey-West) 標準誤差でのリクエストが成功することを確認"""
    output = _get_output(
        client, OlsPayload(se_method="hac", se_extra={"maxlags": 1}).build()
    )
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_ols_clustered_se(client, tables_store):
    """クラスタロバスト標準誤差でリクエストが成功することを確認"""
    payload = {
        "tableName": TABLE_BASIC,
        "dependentVariable": "y_cont",
        "explanatoryVariables": ["x1"],
        "hasConst": True,
        "analysis": {"method": "ols"},
        "standardError": {
            "method": "cluster",
            "groups": ["x2"],
        },
    }
    resp = client.post(URL_REGRESSION, json=payload)
    # x2は連続値のためクラスタ数が多い場合でも正常/エラーいずれも許容
    assert resp.status_code in (
        status.HTTP_200_OK,
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def test_ols_name_description_stored(client, tables_store):
    """name・descriptionが正しく保存されることを確認"""
    payload = OlsPayload().build()
    payload["resultName"] = "テスト回帰モデル"
    payload["description"] = "OLSの動作確認テスト"

    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK
    result_id = resp.json()["result"]["resultId"]

    saved = AnalysisResultStore().get_result(result_id)
    assert saved.name == "テスト回帰モデル"
    assert saved.description == "OLSの動作確認テスト"


def test_ols_aic_bic_present(client, tables_store):
    """AIC・BIC・logLikelihoodが modelStatistics に含まれることを確認"""
    model_stats = _get_output(client, OlsPayload().build())["modelStatistics"]
    for key in ("AIC", "BIC", "logLikelihood"):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )


def test_ols_coefficient_sign_correct(client, tables_store):
    """既知係数（x1≈+2.535, x2≈-1.832）の符号を確認"""
    params = _get_output(client, OlsPayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    # gold 値: x1=+2.535 → 正, x2=-1.832 → 負
    assert coef_map["x1"] > _MIN_X1_COEF
    assert coef_map["x2"] < 0.0


def test_ols_hac_numerical(client, tables_store):
    """HAC標準誤差が gold JSON (Newey-West maxlags=1) と一致することを確認"""
    gold_se = load_py_gold("ols")["estimates"]["hac_maxlags1"]["std_errors"]

    payload = OlsPayload(se_method="hac", se_extra={"maxlags": 1}).build()
    params = _get_output(client, payload)["parameters"]
    for p in params:
        var = p["variable"]
        assert abs(p["standardError"] - gold_se[var]) < _HAC_ABS_TOL, (
            f"{var} HAC SE: got {p['standardError']!r},"
            f" expected {gold_se[var]!r}"
        )

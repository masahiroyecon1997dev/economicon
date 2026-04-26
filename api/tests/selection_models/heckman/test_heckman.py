"""ヘックマン2段階推定テスト"""

from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.selection_models.heckman.conftest import (
    TABLE_HECKMAN,
    URL_HECKMAN,
)

# ---------------------------------------------------------------------------
# ペイロードヘルパー
# ---------------------------------------------------------------------------

_BASE_PAYLOAD: dict = {
    "tableName": TABLE_HECKMAN,
    "dependentVariable": "wage",
    "explanatoryVariables": ["educ", "exp"],
    "selectionColumn": "employed",
    "selectionVariables": ["educ", "exp", "kids"],
    "hasConst": True,
    "reportFirstStage": True,
}


def _payload(**overrides) -> dict:
    return {**_BASE_PAYLOAD, **overrides}


def _get_result_data(client, payload: dict) -> dict:
    """POST してから AnalysisResultStore より result_data を返す。"""
    resp = client.post(URL_HECKMAN, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------


def test_heckman_success(client, tables_store):
    """200 を返し resultId を含むことを確認。"""
    resp = client.post(URL_HECKMAN, json=_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_heckman_response_structure(client, tables_store):
    """result_data に必須キーが含まれることを確認。"""
    rd = _get_result_data(client, _payload())

    assert "parameters" in rd
    assert "modelStatistics" in rd
    assert "diagnostics" in rd
    assert "firstStage" in rd

    ms = rd["modelStatistics"]
    for key in ("nObservations", "R2", "adjustedR2", "logLikelihood"):
        assert key in ms, f"modelStatistics に {key!r} が存在しない"

    diag = rd["diagnostics"]
    assert "inverseMillsRatio" in diag
    imr = diag["inverseMillsRatio"]
    for key in (
        "coefficient",
        "standardError",
        "tValue",
        "pValue",
        "description",
    ):
        assert key in imr, f"inverseMillsRatio に {key!r} が存在しない"
    assert "standardErrorNote" in diag


def test_heckman_lambda_in_parameters(client, tables_store):
    """Step 2 パラメータに lambda（IMR 係数）が含まれることを確認。"""
    rd = _get_result_data(client, _payload())
    params = rd["parameters"]
    # const + educ + exp + lambda = 4 パラメータ
    assert len(params) == 4  # noqa: PLR2004
    assert params[-1]["variable"] == "lambda"
    for key in ("coefficient", "standardError", "tValue", "pValue"):
        assert key in params[-1]


def test_heckman_first_stage_present(client, tables_store):
    """reportFirstStage=true → firstStage が null でないことを確認。"""
    rd = _get_result_data(client, _payload(reportFirstStage=True))
    assert rd["firstStage"] is not None
    fs = rd["firstStage"]
    assert "parameters" in fs
    assert "pseudoR2" in fs
    assert "logLikelihood" in fs
    assert "description" in fs
    # const + educ + exp + kids = 4
    assert len(fs["parameters"]) == 4  # noqa: PLR2004


def test_heckman_first_stage_none_when_false(client, tables_store):
    """reportFirstStage=false → firstStage が null であることを確認。"""
    rd = _get_result_data(client, _payload(reportFirstStage=False))
    assert rd["firstStage"] is None


def test_heckman_result_stored(client, tables_store):
    """resultId で保存済み結果が取得できることを確認。"""
    resp = client.post(URL_HECKMAN, json=_payload())
    assert resp.status_code == status.HTTP_200_OK
    result_id = resp.json()["result"]["resultId"]

    saved = AnalysisResultStore().get_result(result_id)
    assert saved is not None
    assert saved.model_type == "heckman"
    assert saved.has_model_file()


def test_heckman_model_has_both_stages(client, tables_store):
    """pickle に step1_probit と step2_ols が保存されることを確認。"""
    resp = client.post(URL_HECKMAN, json=_payload())
    result_id = resp.json()["result"]["resultId"]

    raw = AnalysisResultStore().get_result(result_id).load_model()
    assert isinstance(raw, dict)
    assert "step1_probit" in raw
    assert "step2_ols" in raw


def test_heckman_no_const(client, tables_store):
    """hasConst=false でも正常に推定できることを確認。"""
    resp = client.post(URL_HECKMAN, json=_payload(hasConst=False))
    assert resp.status_code == status.HTTP_200_OK
    result_id = resp.json()["result"]["resultId"]
    rd = AnalysisResultStore().get_result(result_id).result_data
    params = rd["parameters"]
    # educ + exp + lambda = 3 パラメータ
    assert len(params) == 3  # noqa: PLR2004
    assert params[-1]["variable"] == "lambda"


# ---------------------------------------------------------------------------
# 異常系
# ---------------------------------------------------------------------------


def test_heckman_table_not_found(client, tables_store):
    """存在しないテーブル → 400 を返すことを確認。"""
    resp = client.post(
        URL_HECKMAN, json=_payload(tableName="NonExistentTable")
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_heckman_dependent_variable_not_found(client, tables_store):
    """存在しない被説明変数 → 400 を返すことを確認。"""
    resp = client.post(
        URL_HECKMAN, json=_payload(dependentVariable="no_such_col")
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_heckman_exclusion_restriction_error(client, tables_store):
    """除外制約違反（selectionVariables ⊆ explanatoryVariables）→
    Pydantic model_validator が 422 を返すことを確認。
    """
    resp = client.post(
        URL_HECKMAN,
        json=_payload(
            selectionVariables=["educ", "exp"],
        ),
    )
    # スキーマ層（model_validator）による検証は FastAPI が 422 を返す
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_heckman_selection_column_not_binary_error(client, tables_store):
    """非バイナリ selectionColumn → 400 を返すことを確認。"""
    # wage 列は連続値なので selectionColumn に指定するとエラー
    resp = client.post(
        URL_HECKMAN,
        json=_payload(
            selectionColumn="wage",
            selectionVariables=[
                "educ",
                "exp",
                "kids",
            ],
        ),
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_heckman_selection_column_is_string_type_error(client, tables_store):
    """存在しない selectionColumn → 400（列存在確認）を確認。"""
    resp = client.post(
        URL_HECKMAN,
        json=_payload(selectionColumn="nonexistent_binary"),
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_heckman_imr_coefficient_not_none(client, tables_store):
    """λ 係数・SE・t 値・p 値がすべて数値であることを確認。"""
    rd = _get_result_data(client, _payload())
    imr = rd["diagnostics"]["inverseMillsRatio"]
    for key in ("coefficient", "standardError", "tValue", "pValue"):
        assert imr[key] is not None, f"inverseMillsRatio.{key} が None"
        assert isinstance(imr[key], float), (
            f"inverseMillsRatio.{key} が float でない: {imr[key]!r}"
        )

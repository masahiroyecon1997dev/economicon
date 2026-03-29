"""推定結果フォーマット出力テスト (POST /api/analysis/output-result)"""

import re

from fastapi import status

from economicon.schemas.regressions import OutputResultRequest
from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import (
    AnalysisResultStore,
)
from economicon.services.regressions.output_result import OutputResult
from tests.regressions.conftest import (
    URL_REGRESSION,
    FePayload,
    IvPayload,
    LassoPayload,
    LogitPayload,
    OlsPayload,
)

URL_OUTPUT = "/api/analysis/output-result"

# テスト用定数
_MISSING_ID_1 = "non-existent-id"
_MISSING_ID_2 = "another-missing-id"
_DUMMY_ID = "dummy-id"
_EXPECTED_MISSING_MSG = (
    f"The following analysis results do not exist: {_MISSING_ID_1}"
)


def _run_regression(client, payload) -> str:
    """任意のペイロードで回帰推定を実行して result_id を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload.build())
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["result"]["resultId"]


def _run_ols(client, tables_store) -> str:
    """OLS 推定を実行して result_id を返すヘルパー"""
    return _run_regression(client, OlsPayload())


# -----------------------------------------------------------
# 正常系 — 基本フォーマット
# -----------------------------------------------------------


def test_output_result_text_success(client, tables_store):
    """正常系: text フォーマットで 200 が返る"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "OK" == data["code"]
    result = data["result"]
    assert "content" in result
    assert "format" in result
    assert "text" == result["format"]


def test_output_result_markdown_success(client, tables_store):
    """正常系: markdown フォーマットで 200 が返りテーブルヘッダーを含む"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "markdown"},
    )
    assert resp.status_code == status.HTTP_200_OK
    result = resp.json()["result"]
    assert "markdown" == result["format"]
    assert "| Variable |" in result["content"]


def test_output_result_latex_success(client, tables_store):
    """正常系: latex フォーマットで 200 が返り tabular 環境を含む"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "latex"},
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert r"\begin{table}" in content
    assert r"\end{table}" in content
    assert r"\hline\hline" in content


def test_output_result_contains_variables(client, tables_store):
    """正常系: 出力に説明変数と定数項が含まれる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    content = resp.json()["result"]["content"]
    assert "x1" in content
    assert "x2" in content
    assert "const" in content


def test_output_result_model_stats_present(client, tables_store):
    """正常系: N・R² などのモデル統計行が出力に含まれる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    content = resp.json()["result"]["content"]
    assert "N" in content
    assert "R\u00b2" in content or "R2" in content


def test_output_result_multiple_models(client, tables_store):
    """正常系: 複数モデルを渡すとモデル番号列が 2 つ生成される"""
    id1 = _run_ols(client, tables_store)
    id2 = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [id1, id2], "format": "text"},
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert "(1)" in content
    assert "(2)" in content


# -----------------------------------------------------------
# 正常系 — 変数順序制御
# -----------------------------------------------------------


def test_output_result_const_at_bottom(client, tables_store):
    """正常系: constAtBottom=True のとき const が x1・x2 より後に現れる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "constAtBottom": True,
        },
    )
    content = resp.json()["result"]["content"]
    assert content.index("x1") < content.index("const")
    assert content.index("x2") < content.index("const")


def test_output_result_const_at_top(client, tables_store):
    """正常系: constAtBottom=False のとき const が x1・x2 より前に現れる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "constAtBottom": False,
        },
    )
    content = resp.json()["result"]["content"]
    assert content.index("const") < content.index("x1")
    assert content.index("const") < content.index("x2")


def test_output_result_variable_order_reorders(client, tables_store):
    """正常系: variableOrder=[x2,x1] のとき x2 が x1 より先に現れる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "variableOrder": ["x2", "x1"],
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert content.index("x2") < content.index("x1")


def test_output_result_variable_order_ghost_var_ignored(client, tables_store):
    """
    正常系: variableOrder に存在しない変数が含まれても無視されて正常完了。
    _resolve_variable_order: var not in all_seen 分岐を通過する。
    """
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "variableOrder": ["ghost_var", "x2", "x1"],
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert "ghost_var" not in content
    assert content.index("x2") < content.index("x1")


def test_output_result_variable_order_partial_puts_rest_after(
    client, tables_store
):
    """
    正常系: variableOrder が一部指定のとき、残りは登場順で後に追加される。
    _resolve_variable_order で placed されなかった var が後ろに追加される
    分岐を通過する。
    """
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "variableOrder": ["x2"],
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert content.index("x2") < content.index("x1")


# -----------------------------------------------------------
# 正常系 — variableLabels
# -----------------------------------------------------------


def test_output_result_variable_labels(client, tables_store):
    """正常系: variableLabels で変数名を置換できる"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "variableLabels": {
                "x1": "Income",
                "x2": "Education",
            },
        },
    )
    content = resp.json()["result"]["content"]
    assert "Income" in content
    assert "Education" in content
    assert "x1" not in content
    assert "x2" not in content


# -----------------------------------------------------------
# 正常系 — IV / FE / Logit モデル固有統計量
# -----------------------------------------------------------


def test_output_result_iv_first_stage_f_present(client, tables_store):
    """
    正常系: IV モデルで "1st-F: {内生変数名}" 行が出力に含まれる。
    _first_stage_stat_items / _collect_first_stage_vars の非空パスを通過。
    """
    result_id = _run_regression(client, IvPayload())
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "1st-F:" in resp.json()["result"]["content"]


def test_output_result_fe_r2_within_present(client, tables_store):
    """
    正常系: FE モデルで R² (within) がモデル統計行に含まれる。
    _MODEL_STAT_KEYS の R2Within 行を通過する。
    """
    result_id = _run_regression(client, FePayload())
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    content = resp.json()["result"]["content"]
    assert "R\u00b2 (within)" in content


def test_output_result_logit_pseudo_r2_present(client, tables_store):
    """
    正常系: Logit モデルで Pseudo R² がモデル統計行に含まれる。
    _MODEL_STAT_KEYS の pseudoRSquared 行を通過する。
    """
    result_id = _run_regression(client, LogitPayload())
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    content = resp.json()["result"]["content"]
    assert "Pseudo R" in content


# -----------------------------------------------------------
# 正常系 — LASSO: stat_val=None プレースホルダー + p_value=None 記号
# -----------------------------------------------------------


def test_output_result_lasso_paren_shows_placeholder(client, tables_store):
    """
    正常系: LASSO（SE 未計算）の括弧行は '---' プレースホルダーが表示される。
    _get_coef_paren: stat_val is None → '---' 分岐を通過する。
    _get_stars: p_value is None → return '' 分岐を合わせて通過する。
    """
    result_id = _run_regression(client, LassoPayload())
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "statInParentheses": "se",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "---" in resp.json()["result"]["content"]


# -----------------------------------------------------------
# 正常系 — 複数モデルで一方に変数なし（param=None）
# -----------------------------------------------------------


def test_output_result_multi_model_absent_variable_empty_cell(
    client, tables_store
):
    """
    正常系: x1+x2 モデルと x1 のみのモデルを並置したとき 200 が返る。
    _get_coef_paren: param is None → ('', '') 分岐を通過する。
    """
    id_full = _run_ols(client, tables_store)
    id_x1_only = _run_regression(client, OlsPayload(expl=["x1"]))
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [id_full, id_x1_only], "format": "text"},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "x2" in resp.json()["result"]["content"]


# -----------------------------------------------------------
# 正常系 — significanceStars カスタム設定 / 空配列
# -----------------------------------------------------------


def test_output_result_custom_significance_stars_applied(client, tables_store):
    """正常系: 独自の有意性記号 '+' が設定されて係数に付与される"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "significanceStars": [{"threshold": 0.05, "symbol": "+"}],
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert "+" in content
    assert "***" not in content


def test_output_result_empty_significance_stars_no_symbols(
    client, tables_store
):
    """
    正常系: significanceStars=[] のとき記号が一切付与されない。
    _get_stars: p_value <= threshold が 1 件も成立しない → return '' 分岐
    を通過する。
    """
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "significanceStars": [],
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert "*" not in content


# -----------------------------------------------------------
# 正常系 — statInParentheses 各種値
# -----------------------------------------------------------


def test_output_result_stat_none_no_parentheses(client, tables_store):
    """正常系: statInParentheses='none' のとき括弧付き数値行が出力されない"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "statInParentheses": "none",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    content = resp.json()["result"]["content"]
    assert not re.search(r"\(\d+\.\d+\)", content), (
        "括弧付き数値行が検出された"
    )


def test_output_result_stat_t_in_parentheses(client, tables_store):
    """正常系: statInParentheses='t' のとき括弧付き t 値が出力される"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "statInParentheses": "t",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert re.search(r"\(\d+\.\d+\)", resp.json()["result"]["content"])


def test_output_result_stat_p_in_parentheses(client, tables_store):
    """正常系: statInParentheses='p' のとき括弧付き p 値が出力される"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [result_id],
            "format": "text",
            "statInParentheses": "p",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert re.search(r"\(\d+\.\d+\)", resp.json()["result"]["content"])


def test_output_result_significance_stars_present(client, tables_store):
    """
    正常系: デフォルト有意性記号が係数に付与される（OLS で p<0.01 が存在する）
    """
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "text"},
    )
    assert "***" in resp.json()["result"]["content"]


# -----------------------------------------------------------
# 正常系 — LaTeX 固有: 上付き記号フォーマット
# -----------------------------------------------------------


def test_output_result_latex_stars_superscript_format(client, tables_store):
    """正常系: LaTeX 形式では有意性記号が $^{...}$ 上付き記法で出力される"""
    result_id = _run_ols(client, tables_store)
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [result_id], "format": "latex"},
    )
    content = resp.json()["result"]["content"]
    assert "$^{" in content


# -----------------------------------------------------------
# 正常系 — べき等性
# -----------------------------------------------------------


def test_output_result_idempotent(client, tables_store):
    """
    正常系: 同一パラメータで 2 回リクエストすると content・code が完全一致する
    """
    result_id = _run_ols(client, tables_store)
    payload = {"resultIds": [result_id], "format": "text"}
    r1 = client.post(URL_OUTPUT, json=payload).json()
    r2 = client.post(URL_OUTPUT, json=payload).json()
    assert r1["code"] == r2["code"]
    assert r1["result"]["content"] == r2["result"]["content"]


# -----------------------------------------------------------
# 単体: _fetched=None フォールバックパス
# -----------------------------------------------------------


def test_output_result_execute_without_validate_uses_fallback(
    client, tables_store
):
    """
    単体: validate() を呼ばずに execute() を直接呼んだとき、
    _fetched=None のフォールバック（self._fetched or [...]）を通過する。
    ルーター経由では run_operation が必ず validate() を先に呼ぶため
    API テストでは到達できないパス。
    """

    result_id = _run_ols(client, tables_store)
    req = OutputResultRequest(result_ids=[result_id], format="text")
    svc = OutputResult(req, AnalysisResultStore())

    assert svc._fetched is None  # validate() 未呼び出しを確認
    result = svc.execute()
    assert result["format"] == "text"
    assert len(result["content"]) > 0


# -----------------------------------------------------------
# 異常系 — 400 (DATA_NOT_FOUND)
# -----------------------------------------------------------


def test_output_result_invalid_id_returns_400(client, tables_store):
    """異常系: 存在しない result_id は 400 を返す"""
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [_MISSING_ID_1], "format": "text"},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert "DATA_NOT_FOUND" == data["code"]
    assert _MISSING_ID_1 in data["message"]


def test_output_result_error_message_exact_match(client, tables_store):
    """異常系: エラーメッセージが期待文字列と完全一致する"""
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [_MISSING_ID_1], "format": "text"},
    )
    assert _EXPECTED_MISSING_MSG == resp.json()["message"]


def test_output_result_multiple_missing_ids_comma_separated(
    client, tables_store
):
    """
    異常系: 複数の存在しない result_id は 400 でカンマ区切りのメッセージに
    含まれる。validate() の missing リスト結合ロジックを通過する。
    """
    resp = client.post(
        URL_OUTPUT,
        json={
            "resultIds": [_MISSING_ID_1, _MISSING_ID_2],
            "format": "text",
        },
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    msg = resp.json()["message"]
    assert _MISSING_ID_1 in msg
    assert _MISSING_ID_2 in msg


# -----------------------------------------------------------
# 異常系 — 422 (Pydantic バリデーション)
# -----------------------------------------------------------


def test_output_result_empty_ids_returns_422(client, tables_store):
    """異常系: resultIds が空リストは 422 を返す"""
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [], "format": "text"},
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_output_result_invalid_format_returns_422(client, tables_store):
    """異常系: 不正な format 値（excel）は 422 を返す"""
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [_DUMMY_ID], "format": "excel"},
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_output_result_422_detail_has_loc_and_msg(client, tables_store):
    """
    異常系: 422 のコードが VALIDATION_ERROR で、
    details リストにメッセージが存在する（アプリ内装エラー形式）。
    """
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [], "format": "text"},
    )
    data = resp.json()
    assert "VALIDATION_ERROR" == data["code"]
    assert isinstance(data["details"], list)
    assert len(data["details"]) > 0


def test_output_result_422_no_info_leak(client, tables_store):
    """
    異常系: 422 レスポンスにスタックトレース・内部パス・認証情報が
    含まれないこと（情報漏洩防止）。
    """
    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [], "format": "text"},
    )
    body = resp.text
    assert "Traceback" not in body
    assert "password" not in body.lower()
    assert "api_key" not in body.lower()
    assert "c:\\" not in body.lower()
    assert "/home/" not in body


# -----------------------------------------------------------
# 異常系 — 500 (execute 内予期しない例外)
# -----------------------------------------------------------


def test_output_result_500_on_malformed_regression_output(
    client, tables_store
):
    """
    異常系: dependentVariable キーが欠落した不正な regression_output を
    持つ結果を出力しようとすると 500 が返る。
    execute() の except Exception → ProcessingError 変換分岐を通過する。
    """

    bad = AnalysisResult(
        name="malformed",
        description="test",
        table_name="dummy",
        # dependentVariable キーが欠落 → _RegOutput.__init__ で KeyError
        regression_output={"parameters": []},
    )
    AnalysisResultStore().save_result(bad)

    resp = client.post(
        URL_OUTPUT,
        json={"resultIds": [bad.id], "format": "text"},
    )
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "OUTPUT_RESULT_ERROR" == resp.json()["code"]

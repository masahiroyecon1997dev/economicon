"""診断列追加テスト（予測値・残差の抽出とテーブル統合）"""

from fastapi import status

from economicon.core.enums import ErrorCode
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from tests.regressions.conftest import (
    TABLE_BASIC,
    TABLE_IV,
    TABLE_NAN,
    TABLE_PANEL,
    TABLE_TOBIT,
    URL_REGRESSION,
    IvPayload,
    LassoPayload,
    OlsPayload,
    RidgePayload,
)

URL_ADD_DIAGNOSTIC = "/api/analysis/regression/add-diagnostic-columns"

# -----------------------------------------------------------
# ヘルパー
# -----------------------------------------------------------


def _run_regression(client, payload: dict) -> str:
    """回帰を実行して result_id を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return resp.json()["result"]["resultId"]


def _add_diagnostic(client, body: dict) -> dict:
    """診断列追加エンドポイントを呼び出して result を返すヘルパー"""
    resp = client.post(URL_ADD_DIAGNOSTIC, json=body)
    return resp


def _get_table_columns(table_name: str) -> list[str]:
    """TablesStore から列名リストを取得"""
    return TablesStore().get_column_name_list(table_name)


# -----------------------------------------------------------
# OLS 正常系
# -----------------------------------------------------------


def test_ols_fitted_values_added(client, tables_store):
    """OLS モデルから fitted values が追加されることを確認"""
    result_id = _run_regression(client, OlsPayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    data = resp.json()
    assert data["code"] == "OK"
    assert data["result"]["tableName"] == TABLE_BASIC
    added_cols = data["result"]["addedColumns"]
    assert len(added_cols) == 1
    assert "y_linear_fitted" in added_cols

    # テーブルに列が存在することを確認
    cols = _get_table_columns(TABLE_BASIC)
    assert "y_linear_fitted" in cols


def test_ols_residuals_added(client, tables_store):
    """OLS モデルから残差が追加されることを確認"""
    result_id = _run_regression(client, OlsPayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "residual",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_linear_resid" in added_cols
    assert "y_linear_fitted" not in added_cols


def test_ols_residuals_standardized(client, tables_store):
    """OLS モデルから標準化残差が追加されることを確認"""
    result_id = _run_regression(client, OlsPayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "residual",
            "standardized": True,
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_linear_resid" in added_cols
    assert "y_linear_resid_std" in added_cols


def test_ols_both_with_interval(client, tables_store):
    """OLS から fitted + resid + 95%CI が同時追加されることを確認"""
    result_id = _run_regression(client, OlsPayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "both",
            "includeInterval": True,
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_linear_fitted" in added_cols
    assert "y_linear_fitted_lower_95" in added_cols
    assert "y_linear_fitted_upper_95" in added_cols
    assert "y_linear_resid" in added_cols


def test_ols_column_values_are_finite(client, tables_store):
    """追加された列の値が有限値（NaN/null なし）であることを確認"""
    result_id = _run_regression(client, OlsPayload().build())
    _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    df = TablesStore().get_table(TABLE_BASIC).table
    assert df["y_linear_fitted"].null_count() == 0
    assert df["y_linear_fitted"].is_nan().sum() == 0


# -----------------------------------------------------------
# 列名重複の解決
# -----------------------------------------------------------


def test_column_name_deduplication(client, tables_store):
    """同名列が存在する場合に _0, _1 が付くことを確認"""
    result_id = _run_regression(client, OlsPayload().build())

    # 1回目：y_linear_fitted が追加される
    _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    # 2回目：y_linear_fitted が既に存在するため y_linear_fitted_0 が追加される
    resp2 = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    assert resp2.status_code == status.HTTP_200_OK, resp2.text
    added_cols2 = resp2.json()["result"]["addedColumns"]
    assert "y_linear_fitted_0" in added_cols2

    # 3回目：y_linear_fitted_0 も存在するため y_linear_fitted_1 が追加される
    resp3 = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "fitted",
        },
    )
    assert resp3.status_code == status.HTTP_200_OK, resp3.text
    added_cols3 = resp3.json()["result"]["addedColumns"]
    assert "y_linear_fitted_1" in added_cols3


# -----------------------------------------------------------
# 欠損値含むデータでの行整合性確認
# -----------------------------------------------------------


def test_missing_row_alignment(client, tables_store):
    """
    欠損値を含むデータで推定後の診断列が正しく join されることを確認

    NaNData には欠損値が含まれるため、推定に使われた行数が元テーブルより少ない。
    追加後のテーブルは元の 10 行を保ち、欠損行は null になるべき。
    """
    result_id = _run_regression(
        client,
        {
            "tableName": TABLE_NAN,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": True,
            "analysis": {"method": "ols"},
            "standardError": {"method": "nonrobust"},
        },
    )

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_NAN,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text

    df = TablesStore().get_table(TABLE_NAN).table
    # 元テーブルの行数は 10 行のまま
    assert df.height == 10
    # 欠損行に対応する fitted は null になっているはず
    assert df["y_fitted"].null_count() > 0
    # 欠損のない行には有効な値が入っているはず
    assert df["y_fitted"].drop_nulls().len() > 0


# -----------------------------------------------------------
# Tobit
# -----------------------------------------------------------


def test_tobit_fitted_and_resid(client, tables_store):
    """Tobit モデルから予測値・残差が追加されることを確認"""
    result_id = _run_regression(
        client,
        {
            "tableName": TABLE_TOBIT,
            "dependentVariable": "y",
            "explanatoryVariables": ["x"],
            "hasConst": True,
            "analysis": {
                "method": "tobit",
                "leftCensoringLimit": 0.0,
                "rightCensoringLimit": None,
            },
            "standardError": {"method": "nonrobust"},
        },
    )

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_TOBIT,
            "resultId": result_id,
            "target": "both",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_fitted" in added_cols
    assert "y_resid" in added_cols

    df = TablesStore().get_table(TABLE_TOBIT).table
    assert df["y_fitted"].null_count() == 0


# -----------------------------------------------------------
# Fixed Effects (FE)
# -----------------------------------------------------------


def test_fe_fitted_total(client, tables_store):
    """FE モデルから total effects の予測値が追加されることを確認"""
    result_id = _run_regression(
        client,
        {
            "tableName": TABLE_PANEL,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": False,
            "analysis": {
                "method": "fe",
                "entityIdColumn": "entity_id",
                "timeColumn": "time_id",
            },
            "standardError": {"method": "nonrobust"},
        },
    )

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_PANEL,
            "resultId": result_id,
            "target": "fitted",
            "feType": "total",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_fitted" in added_cols


def test_fe_fitted_within(client, tables_store):
    """FE モデルから within effects の予測値が追加されることを確認"""
    result_id = _run_regression(
        client,
        {
            "tableName": TABLE_PANEL,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": False,
            "analysis": {
                "method": "fe",
                "entityIdColumn": "entity_id",
                "timeColumn": "time_id",
            },
            "standardError": {"method": "nonrobust"},
        },
    )

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_PANEL,
            "resultId": result_id,
            "target": "fitted",
            "feType": "within",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_fitted" in added_cols

    df = TablesStore().get_table(TABLE_PANEL).table
    assert df["y_fitted"].null_count() == 0


def test_fe_residuals(client, tables_store):
    """FE モデルから残差が追加されることを確認"""
    result_id = _run_regression(
        client,
        {
            "tableName": TABLE_PANEL,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": False,
            "analysis": {
                "method": "fe",
                "entityIdColumn": "entity_id",
                "timeColumn": "time_id",
            },
            "standardError": {"method": "nonrobust"},
        },
    )

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_PANEL,
            "resultId": result_id,
            "target": "residual",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_resid" in added_cols


# -----------------------------------------------------------
# Random Effects (RE)
# -----------------------------------------------------------


def test_re_fitted_values_added(client, tables_store):
    """RE モデルから予測値が追加されることを確認"""
    result_id = _run_regression(
        client,
        {
            "tableName": TABLE_PANEL,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": True,
            "analysis": {
                "method": "re",
                "entityIdColumn": "entity_id",
                "timeColumn": "time_id",
            },
            "standardError": {"method": "nonrobust"},
        },
    )

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_PANEL,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_fitted" in added_cols


# -----------------------------------------------------------
# IV (2SLS)
# -----------------------------------------------------------


def test_iv_fitted_residuals(client, tables_store):
    """IV モデルから予測値・構造残差が追加されることを確認"""
    result_id = _run_regression(client, IvPayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_IV,
            "resultId": result_id,
            "target": "both",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_fitted" in added_cols
    assert "y_resid" in added_cols

    df = TablesStore().get_table(TABLE_IV).table
    assert df["y_fitted"].null_count() == 0


# -----------------------------------------------------------
# Ridge
# -----------------------------------------------------------


def test_ridge_fitted_values_added(client, tables_store):
    """Ridge モデルから予測値が追加されることを確認"""
    result_id = _run_regression(client, RidgePayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_linear_fitted" in added_cols


def test_ridge_residuals(client, tables_store):
    """Ridge モデルから残差が追加されることを確認"""
    result_id = _run_regression(client, RidgePayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "residual",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_linear_resid" in added_cols


# -----------------------------------------------------------
# Lasso
# -----------------------------------------------------------


def test_lasso_fitted_values_added(client, tables_store):
    """Lasso モデルから予測値が追加されることを確認"""
    result_id = _run_regression(client, LassoPayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "both",
        },
    )

    assert resp.status_code == status.HTTP_200_OK, resp.text
    added_cols = resp.json()["result"]["addedColumns"]
    assert "y_linear_fitted" in added_cols
    assert "y_linear_resid" in added_cols


# -----------------------------------------------------------
# エラー系
# -----------------------------------------------------------


def test_result_id_not_found(client, tables_store):
    """存在しない result_id を指定した場合に 400 が返ることを確認"""
    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": "00000000-0000-0000-0000-000000000000",
            "target": "fitted",
        },
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.text
    data = resp.json()
    assert data["code"] == ErrorCode.DATA_NOT_FOUND


def test_table_not_found(client, tables_store):
    """存在しないテーブル名を指定した場合に 400 が返ることを確認"""
    result_id = _run_regression(client, OlsPayload().build())

    resp = _add_diagnostic(
        client,
        {
            "tableName": "NonExistentTable",
            "resultId": result_id,
            "target": "fitted",
        },
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.text


def test_model_file_not_found(client, tables_store):
    """pkl ファイルが存在しない場合に 400 が返ることを確認"""
    result_id = _run_regression(client, OlsPayload().build())

    # pkl ファイルを手動削除して「ファイルなし」状態を作る
    result_store = AnalysisResultStore()
    analysis_result = result_store.get_result(result_id)
    analysis_result.delete_model_file()

    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.text
    data = resp.json()
    assert data["code"] == ErrorCode.MODEL_FILE_NOT_FOUND


def test_fe_key_column_not_in_table(client, tables_store):
    """
    FE モデルの entity_id_column が対象テーブルに存在しない場合に
    400 (MODEL_KEY_MISMATCH) が返ることを確認
    """
    # FE 推定は PanelData で実行
    result_id = _run_regression(
        client,
        {
            "tableName": TABLE_PANEL,
            "dependentVariable": "y",
            "explanatoryVariables": ["x1", "x2"],
            "hasConst": False,
            "analysis": {
                "method": "fe",
                "entityIdColumn": "entity_id",
                "timeColumn": "time_id",
            },
            "standardError": {"method": "nonrobust"},
        },
    )

    # 追加先は BasicData（entity_id / time_id が存在しない）
    resp = _add_diagnostic(
        client,
        {
            "tableName": TABLE_BASIC,
            "resultId": result_id,
            "target": "fitted",
        },
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.text
    data = resp.json()
    assert data["code"] == ErrorCode.MODEL_KEY_MISMATCH

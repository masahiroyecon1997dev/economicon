"""ヘックマン2段階推定サービス

推定理論:
  Step 1: s_i = 1[z_i'γ + ε_i > 0]  (Probit・全サンプル)
  Step 2: y_i = x_i'β + ρ·λ(z_i'γ̂) + u_i  (OLS・選択サンプル)

  λ(·) = φ(·)/Φ(·) : 逆ミルズ比 (Inverse Mills Ratio)
  ρ = σ_12/σ_2  : セレクションバイアス係数

  λ の係数 ρ が有意 → セレクションバイアスが存在。
"""

import logging
from typing import Any, ClassVar

import numpy as np
import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.heckman import HeckmanRequestBody
from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import (
    MISSING_HANDLING_MAP,
    extract_statsmodels_params,
)
from economicon.utils import ProcessingError, ValidationError
from economicon.utils.column_names import generate_unique_column_name
from economicon.utils.validators import (
    validate_existence,
    validate_numeric_types,
)

_logger = logging.getLogger(__name__)

_PARAM_NAMES: dict[str, str] = {
    "table_name": "tableName",
    "dependent_variable": "dependentVariable",
    "explanatory_variables": "explanatoryVariables",
    "selection_column": "selectionColumn",
    "selection_variables": "selectionVariables",
}


class HeckmanRegression:
    """
    ヘックマン2段階推定 DataOperation 実装。

    _RegressionBase は継承しない（standard_error フィールドが
    不要・選択方程式固有の検証があるため）。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = _PARAM_NAMES

    def __init__(
        self,
        body: HeckmanRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        self.tables_store = tables_store
        self.result_store = result_store
        self.table_name = body.table_name
        self.result_name = body.result_name
        self.description = body.description
        self.dependent_variable = body.dependent_variable
        self.explanatory_variables = body.explanatory_variables
        self.selection_column = body.selection_column
        self.selection_variables = body.selection_variables
        self.has_const = body.has_const
        self.missing_value_handling = body.missing_value_handling
        self.report_first_stage = body.report_first_stage
        self.missing: str = MISSING_HANDLING_MAP.get(
            self.missing_value_handling, "drop"
        )

    # ------------------------------------------------------------------
    # バリデーション
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """入力値の事前検証。"""
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=_PARAM_NAMES["table_name"],
        )

        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        df_schema = self.tables_store.get_schema(self.table_name)

        validate_existence(
            value=self.dependent_variable,
            valid_list=column_name_list,
            target=_PARAM_NAMES["dependent_variable"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=[self.dependent_variable],
            target=_PARAM_NAMES["dependent_variable"],
        )

        validate_existence(
            value=self.explanatory_variables,
            valid_list=column_name_list,
            target=_PARAM_NAMES["explanatory_variables"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=self.explanatory_variables,
            target=_PARAM_NAMES["explanatory_variables"],
        )

        validate_existence(
            value=self.selection_column,
            valid_list=column_name_list,
            target=_PARAM_NAMES["selection_column"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=[self.selection_column],
            target=_PARAM_NAMES["selection_column"],
        )

        validate_existence(
            value=self.selection_variables,
            valid_list=column_name_list,
            target=_PARAM_NAMES["selection_variables"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=self.selection_variables,
            target=_PARAM_NAMES["selection_variables"],
        )

        # selectionColumn が 0/1 バイナリであることを確認
        df = self.tables_store.get_table(self.table_name).table
        non_binary = (
            df.select(pl.col(self.selection_column).drop_nulls())
            .filter(
                ~pl.col(self.selection_column)
                .cast(pl.Float64)
                .is_in([0.0, 1.0])
            )
            .height
        )
        if non_binary > 0:
            raise ValidationError(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=_(
                    "'{}' must be a binary (0/1) dummy variable."
                    " Found {} non-binary value(s)."
                ).format(_PARAM_NAMES["selection_column"], non_binary),
            )

    # ------------------------------------------------------------------
    # 推定
    # ------------------------------------------------------------------

    def execute(self) -> dict:  # noqa: C901, PLR0912, PLR0915
        """ヘックマン2段階推定を実行して結果 ID を返す。"""
        try:
            import statsmodels.api as sm  # noqa: PLC0415
            from scipy.stats import norm  # noqa: PLC0415

            df = self.tables_store.get_table(self.table_name).table

            # 必要な列のみ選択 + 元行インデックスを付与
            all_cols = list(
                {
                    self.selection_column,
                    self.dependent_variable,
                    *self.selection_variables,
                    *self.explanatory_variables,
                }
            )
            orig_idx_col = generate_unique_column_name(
                "__orig_idx__",
                all_cols,
            )
            df_indexed = df.select(all_cols).with_row_index(orig_idx_col)

            # 欠損値処理
            if self.missing == "drop":
                df_clean = df_indexed.drop_nulls()
            elif self.missing == "raise":
                null_total = sum(
                    df_indexed.drop(orig_idx_col).null_count().row(0)
                )
                if null_total > 0:
                    raise ProcessingError(
                        error_code=ErrorCode.MISSING_VALUES_FOUND,
                        message=_("Missing values found in data"),
                    )
                df_clean = df_indexed
            else:
                df_clean = df_indexed

            if df_clean.height == 0:
                raise ProcessingError(
                    error_code=ErrorCode.NO_VALID_OBSERVATIONS,
                    message=_(
                        "No valid observations after removing missing values"
                    ),
                )

            # ============================================================
            # Step 1: Probit（全サンプル・選択方程式）
            # Eco-Note: 選択方程式には識別のため常に定数項を付与する。
            # has_const は結果方程式（Step 2）のみ制御する。
            # ============================================================
            y_sel = df_clean[self.selection_column].to_numpy().astype(float)
            x_sel_raw = df_clean[self.selection_variables].to_numpy()
            x_sel = sm.add_constant(x_sel_raw, has_constant="skip")

            try:
                probit_result = sm.Probit(y_sel, x_sel).fit(disp=False)
            except Exception as exc:
                raise ProcessingError(
                    error_code=ErrorCode.HECKMAN_REGRESSION_PROCESS_ERROR,
                    message=_("Step 1 Probit failed to converge: {}").format(
                        str(exc)
                    ),
                ) from exc

            # ============================================================
            # 逆ミルズ比 (IMR) の計算
            # Eco-Note:
            #   xβ = Probit 線形インデックス（正規分位点）
            #   IMR = φ(xβ) / Φ(xβ)
            #   φ: 標準正規 PDF, Φ: 標準正規 CDF
            # ============================================================
            xb = probit_result.predict(linear=True)
            imr_all = norm.pdf(xb) / norm.cdf(xb)

            # ============================================================
            # Step 2: OLS + IMR（選択サンプルのみ）
            # Eco-Note: IMR は generated regressor であるため
            # 通常の OLS SE は不一致。HC1 robust SE を適用する。
            # ============================================================
            sel_mask = y_sel.astype(bool)
            n_selected = int(sel_mask.sum())
            if n_selected == 0:
                raise ProcessingError(
                    error_code=ErrorCode.NO_VALID_OBSERVATIONS,
                    message=_(
                        "No selected observations"
                        " (selectionColumn has no value = 1)."
                    ),
                )

            y_out = df_clean[self.dependent_variable].to_numpy()[sel_mask]
            x_out_raw = df_clean[self.explanatory_variables].to_numpy()[
                sel_mask
            ]
            imr_selected = imr_all[sel_mask]

            if self.has_const:
                x_out_base = sm.add_constant(x_out_raw, has_constant="skip")
                x_out = np.column_stack([x_out_base, imr_selected])
            else:
                x_out = np.column_stack([x_out_raw, imr_selected])

            # 完全多重共線性チェック
            if np.linalg.matrix_rank(x_out) < x_out.shape[1]:
                raise ProcessingError(
                    error_code=ErrorCode.REGRESSION_SINGULAR_MATRIX_ERROR,
                    message=_(
                        "Explanatory variable matrix is singular."
                        " Perfect multicollinearity detected."
                    ),
                )

            ols_result = sm.OLS(y_out, x_out).fit(cov_type="HC1")

            # ============================================================
            # 結果整形
            # ============================================================
            param_names_step2 = (
                (["const"] if self.has_const else [])
                + self.explanatory_variables
                + ["lambda"]
            )
            params_info = extract_statsmodels_params(
                ols_result, param_names_step2
            )

            # λ（IMR 係数）を diagnostics に抽出
            lambda_info = params_info[-1]
            p_val = lambda_info.get("pValue")
            if p_val is not None and p_val < 0.05:  # noqa: PLR2004
                lambda_desc = _(
                    "Significant lambda indicates selection bias."
                    " Heckman correction is appropriate."
                )
            else:
                lambda_desc = _(
                    "Non-significant lambda. Selection bias may be"
                    " absent, but Heckman correction is retained."
                )

            model_stats: dict[str, Any] = {
                "nObservations": int(ols_result.nobs),
            }
            for attr, key in [
                ("rsquared", "R2"),
                ("rsquared_adj", "adjustedR2"),
                ("llf", "logLikelihood"),
                ("aic", "AIC"),
                ("bic", "BIC"),
            ]:
                if hasattr(ols_result, attr):
                    model_stats[key] = float(getattr(ols_result, attr))

            diagnostics: dict[str, Any] = {
                "inverseMillsRatio": {
                    "coefficient": lambda_info.get("coefficient"),
                    "standardError": lambda_info.get("standardError"),
                    "tValue": lambda_info.get("tValue"),
                    "pValue": p_val,
                    "description": lambda_desc,
                },
                "standardErrorNote": _(
                    "HC1 robust SE applied to Step 2 OLS."
                    " OLS SE is inconsistent due to the"
                    " generated regressor (IMR)."
                ),
            }

            # 第 1 段階レポート
            first_stage: dict[str, Any] | None = None
            if self.report_first_stage:
                param_names_step1 = ["const"] + self.selection_variables
                params_info_step1 = extract_statsmodels_params(
                    probit_result, param_names_step1
                )
                first_stage = {
                    "parameters": params_info_step1,
                    "pseudoR2": (
                        float(probit_result.prsquared)
                        if hasattr(probit_result, "prsquared")
                        else None
                    ),
                    "logLikelihood": float(probit_result.llf),
                    "description": _(
                        "First stage Probit (selection equation)"
                    ),
                }

            regression_output: dict[str, Any] = {
                "tableName": self.table_name,
                "dependentVariable": self.dependent_variable,
                "explanatoryVariables": self.explanatory_variables,
                "selectionColumn": self.selection_column,
                "selectionVariables": self.selection_variables,
                "regressionResult": str(ols_result.summary()),
                "parameters": params_info,
                "modelStatistics": model_stats,
                "diagnostics": diagnostics,
                "firstStage": first_stage,
            }

            # 選択サンプルの元テーブル行インデックス
            # （add_diagnostic_columns での行アライメントに使用）
            orig_indices = (
                df_clean[orig_idx_col].to_numpy()[sel_mask].astype(np.int64)
            )

            # Step 1 (Probit) + Step 2 (OLS) を両方 pickle 保存
            raw_model = {
                "step1_probit": probit_result,
                "step2_ols": ols_result,
            }
            result_id = self._save_result(
                regression_output, raw_model, orig_indices
            )
            return {"resultId": result_id}

        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.HECKMAN_REGRESSION_PROCESS_ERROR,
                message=_("Heckman estimation failed: {}").format(str(e)),
            ) from e

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    def _save_result(
        self,
        regression_output: dict,
        raw_model: dict,
        row_indices: np.ndarray | None = None,
    ) -> str:
        """AnalysisResult を生成・保存し result_id を返す。"""
        if self.result_name:
            name = self.result_name
        else:
            seq = self.result_store.next_sequence("regression")
            name = _("HECKMAN: {dep} #{seq}").format(
                dep=self.dependent_variable,
                seq=seq,
            )
        analysis_result = AnalysisResult(
            name=name,
            description=self.description,
            table_name=self.table_name,
            result_data=regression_output,
            result_type="regression",
            model_type="heckman",
            row_indices=row_indices,
        )
        result_id = self.result_store.save_result(analysis_result)
        analysis_result.save_model(raw_model)
        return result_id

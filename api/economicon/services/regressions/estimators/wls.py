"""WLS（重み付き最小二乗法）回帰モデル"""

import numpy as np
import polars as pl

from economicon.core.enums import ErrorCode
from economicon.schemas.regression_params import WLSParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import prepare_basic_data
from economicon.services.regressions.estimators._base import _RegressionBase
from economicon.services.regressions.fitters import fit_wls
from economicon.services.regressions.formatters import (
    build_groups_arrays,
    format_statsmodels_result,
)
from economicon.services.regressions.standard_errors import (
    apply_standard_errors,
)
from economicon.services.regressions.validators import (
    validate_base_params,
    validate_wls_weights,
)
from economicon.utils import ProcessingError


class WLSRegression(_RegressionBase):
    """WLS 回帰 DataOperation 実装。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: WLSParams = body.analysis  # type: ignore[assignment]

    def validate(self) -> None:
        column_name_list, df_schema = validate_base_params(
            self.table_name,
            self.dependent_variable,
            self.explanatory_variables,
            self.tables_store,
        )
        validate_wls_weights(
            self.analysis.weights_column,
            column_name_list,
            df_schema,
            self.tables_store,
            self.table_name,
        )

    def execute(self) -> dict:
        try:
            df = self.tables_store.get_table(self.table_name).table
            y_data, x_data = prepare_basic_data(
                df,
                self.dependent_variable,
                self.explanatory_variables,
                self.has_const,
                self.missing,
            )
            # 重みベクトルを抽出（欠損行は prepare_basic_data の missing 処理
            # と整合させるため、y_data と同じ長さになるよう NaN を除去する）
            weights_raw = (
                df[self.analysis.weights_column].cast(pl.Float64).to_numpy()
            )
            y_raw = df[self.dependent_variable].cast(pl.Float64).to_numpy()
            x_cols = df[self.explanatory_variables].cast(pl.Float64).to_numpy()
            valid_mask = (
                ~np.isnan(y_raw)
                & ~np.isnan(weights_raw)
                & ~np.isnan(x_cols).any(axis=1)
            )
            weights = weights_raw[valid_mask]

            model_result = fit_wls(y_data, x_data, weights, self.missing)
            model_result = apply_standard_errors(
                model_result,
                self.standard_error,
                groups_arrays=build_groups_arrays(
                    df, y_data, x_data, self.standard_error
                ),
            )
            regression_output = format_statsmodels_result(
                model_result,
                self.table_name,
                self.dependent_variable,
                self.explanatory_variables,
                self.has_const,
            )
            result_id = self._save_result(
                regression_output, model_result, "wls"
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e

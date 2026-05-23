"""FGLS（実行可能一般化最小二乗法）回帰モデル"""

from economicon.core.enums import ErrorCode
from economicon.schemas.regression_params import FGLSParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import prepare_basic_data
from economicon.services.regressions.estimators._base import _RegressionBase
from economicon.services.regressions.fitters import (
    fit_fgls_ar1,
    fit_fgls_heteroskedastic,
)
from economicon.services.regressions.formatters import (
    build_groups_arrays,
    format_statsmodels_result,
)
from economicon.services.regressions.standard_errors import (
    apply_standard_errors,
)
from economicon.services.regressions.validators import validate_base_params
from economicon.utils import ProcessingError


class FGLSRegression(_RegressionBase):
    """FGLS 回帰 DataOperation 実装。

    Eco-Note:
    - fgls_method="heteroskedastic": OLS 残差 ê_i を用いた1ステップ FGLS。
      不均一分散の構造が未知の場合の近似として使う。
    - fgls_method="ar1": sm.GLSAR による AR(1) FGLS。
      系列相関が疑われる時系列データに有効。
    """

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: FGLSParams = body.analysis  # type: ignore[assignment]

    def validate(self) -> None:
        validate_base_params(
            self.table_name,
            self.dependent_variable,
            self.explanatory_variables,
            self.tables_store,
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

            if self.analysis.fgls_method == "ar1":
                model_result = fit_fgls_ar1(
                    y_data,
                    x_data,
                    self.analysis.max_iter,
                    self.missing,
                )
            else:
                # デフォルト: heteroskedastic（1ステップ FGLS）
                model_result = fit_fgls_heteroskedastic(
                    y_data, x_data, self.missing
                )

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
                regression_output, model_result, "fgls"
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e

"""OLS 回帰モデル"""

from economicon.core.enums import ErrorCode
from economicon.schemas.entities import OLSParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import prepare_basic_data
from economicon.services.regressions.fitters import fit_ols
from economicon.services.regressions.formatters import (
    build_groups_arrays,
    format_statsmodels_result,
)
from economicon.services.regressions.models._base import _RegressionBase
from economicon.services.regressions.standard_errors import (
    apply_standard_errors,
)
from economicon.services.regressions.validators import validate_base_params
from economicon.utils import ProcessingError


class OLSRegression(_RegressionBase):
    """OLS 回帰 DataOperation 実装。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: OLSParams = body.analysis  # type: ignore[assignment]

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
            model_result = fit_ols(y_data, x_data, self.missing)
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
                regression_output, model_result, "ols"
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e

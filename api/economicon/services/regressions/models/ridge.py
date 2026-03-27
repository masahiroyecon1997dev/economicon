"""Ridge 正則化回帰モデル"""

from economicon.core.enums import ErrorCode
from economicon.schemas.entities import RidgeParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import prepare_basic_data
from economicon.services.regressions.fitters import (
    RegularizedRegressionInput,
    fit_ridge,
)
from economicon.services.regressions.formatters import (
    format_regularized_result,
)
from economicon.services.regressions.models._base import _RegressionBase
from economicon.services.regressions.validators import validate_base_params
from economicon.utils import ProcessingError


class RidgeRegression(_RegressionBase):
    """Ridge 回帰 DataOperation 実装。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: RidgeParams = body.analysis  # type: ignore[assignment]

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
            data_input = RegularizedRegressionInput(
                y_data=y_data,
                x_data=x_data,
                has_const=self.has_const,
                alpha=self.analysis.alpha,
                missing=self.missing,
                calculate_se=self.analysis.calculate_se,
                bootstrap_iterations=self.analysis.bootstrap_iterations,
                random_state=self.analysis.random_state,
                max_iter=self.analysis.max_iter,
                alpha_convention=self.analysis.alpha_convention,
            )
            reg_result = fit_ridge(data_input)
            regression_output = format_regularized_result(
                reg_result,
                self.table_name,
                self.dependent_variable,
                self.explanatory_variables,
            )
            result_id = self._save_result(
                regression_output, reg_result, "ridge"
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e

"""Probit 回帰モデル"""

from economicon.core.enums import ErrorCode
from economicon.schemas.entities import ProbitParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import prepare_basic_data
from economicon.services.regressions.fitters import fit_probit
from economicon.services.regressions.formatters import (
    build_groups_arrays,
    compute_ame,
    format_statsmodels_result,
)
from economicon.services.regressions.models._base import _RegressionBase
from economicon.services.regressions.standard_errors import (
    get_discrete_fit_kwargs,
)
from economicon.services.regressions.validators import validate_base_params
from economicon.utils import ProcessingError


class ProbitRegression(_RegressionBase):
    """Probit 回帰 DataOperation 実装。"""

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: ProbitParams = body.analysis  # type: ignore[assignment]

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
            fit_kwargs = get_discrete_fit_kwargs(
                self.standard_error,
                groups_arrays=build_groups_arrays(
                    df, y_data, x_data, self.standard_error
                ),
            )
            model_result = fit_probit(
                y_data, x_data, self.missing, **fit_kwargs
            )
            regression_output = format_statsmodels_result(
                model_result,
                self.table_name,
                self.dependent_variable,
                self.explanatory_variables,
                self.has_const,
            )
            if self.analysis.calculate_marginal_effects:
                regression_output["marginalEffects"] = compute_ame(
                    model_result, self.has_const, self.explanatory_variables
                )
            result_id = self._save_result(
                regression_output, model_result, "probit"
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e

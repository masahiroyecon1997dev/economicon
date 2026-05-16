"""GLS（一般化最小二乗法）回帰モデル（既知の分散共分散行列）"""

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.schemas.enums import MissingValueHandlingType
from economicon.schemas.regression_params import GLSParams
from economicon.schemas.regressions import RegressionRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import prepare_basic_data
from economicon.services.regressions.estimators._base import _RegressionBase
from economicon.services.regressions.fitters import fit_gls
from economicon.services.regressions.formatters import (
    build_groups_arrays,
    format_statsmodels_result,
)
from economicon.services.regressions.standard_errors import (
    apply_standard_errors,
)
from economicon.services.regressions.validators import (
    validate_base_params,
    validate_gls_sigma,
)
from economicon.utils import ProcessingError
from economicon.utils.exceptions import ValidationError


class GLSRegression(_RegressionBase):
    """GLS 回帰 DataOperation 実装（既知の分散共分散行列使用）。

    Eco-Note: GLS 使用時は欠損値処理を "error" 固定にする。
    sigma テーブルの次元 n×n が分析テーブルの観測数と一致しなければ
    バリデーションエラーを送出する。
    """

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ) -> None:
        super().__init__(body, tables_store, result_store)
        self.analysis: GLSParams = body.analysis  # type: ignore[assignment]

    def validate(self) -> None:
        # GLS は欠損値 "error" 固定（sigma 次元とサンプル数を確定させるため）
        if self.missing_value_handling != MissingValueHandlingType.ERROR:
            raise ValidationError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=(
                    "GLS requires missingValueHandling='error'."
                    " Please remove rows with missing values"
                    " before using GLS."
                ),
                target="missingValueHandling",
            )

        validate_base_params(
            self.table_name,
            self.dependent_variable,
            self.explanatory_variables,
            self.tables_store,
        )

        # sigma テーブルの次元チェック（観測数 = テーブル行数）
        n_obs = self.tables_store.get_table(self.table_name).table.height
        validate_gls_sigma(
            self.analysis.sigma_table_name,
            n_obs,
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

            # sigma テーブルを n×n NumPy 行列に変換
            sigma_df = self.tables_store.get_table(
                self.analysis.sigma_table_name
            ).table
            sigma = sigma_df.cast(pl.Float64).to_numpy()

            model_result = fit_gls(y_data, x_data, sigma)
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
                regression_output, model_result, "gls"
            )
            return {"resultId": result_id}
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {e}",
            ) from e

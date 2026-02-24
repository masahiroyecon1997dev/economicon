from typing import Any

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import (
    BinaryChoiceRegressionParams,
    InstrumentalVariablesParams,
    OLSParams,
    PanelDataParams,
    RegressionMethodType,
    RegressionRequestBody,
    RegularizedRegressionParams,
    TobitParams,
)
from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.common import (
    MISSING_HANDLING_MAP,
    IvDataConfig,
    PanelDataConfig,
    extract_linearmodels_params,
    extract_statsmodels_params,
    prepare_basic_data,
    prepare_iv_dataframe,
    prepare_panel_dataframe,
    prepare_tobit_dataframe,
)
from economicon.services.regressions.fitters import (
    IVInput,
    RegularizedRegressionInput,
    TobitInput,
    fit_fe,
    fit_iv,
    fit_lasso,
    fit_logit,
    fit_ols,
    fit_probit,
    fit_re,
    fit_ridge,
    fit_tobit,
)
from economicon.services.regressions.standard_errors import (
    apply_standard_errors,
)
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_numeric_types,
)


class Regression:
    """
    回帰分析を実行するためのAPIクラス

    指定された分析タイプに基づいて、適切な回帰分析を実行します。
    """

    def __init__(
        self,
        body: RegressionRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ):
        self.tables_store = tables_store
        self.result_store = result_store
        self.table_info = None
        self.table_name = body.table_name
        self.result_name = body.result_name
        self.description = body.description
        self.dependent_variable = body.dependent_variable
        self.explanatory_variables = body.explanatory_variables
        self.has_const = body.has_const
        self.missing_value_handling = body.missing_value_handling
        self.analysis = body.analysis
        self.standard_error = body.standard_error

        self.param_names = {
            "type": "type",
            "method": "method",
            "table_name": "tableName",
            "name": "name",
            "description": "description",
            "dependent_variable": "dependentVariable",
            "explanatory_variables": "explanatoryVariables",
            "standard_error_method": "standardErrorMethod",
            "standard_error_params": "standardErrorParams",
            "hyper_parameters": "hyperParameters",
            "use_t_distribution": "useTDistribution",
            "has_const": "hasConst",
            "missing_value_handling": "missingValueHandling",
            "entity_id_column": "entityIdColumn",
            "time_column": "timeColumn",
            "instrumental_variables": "instrumentalVariables",
            "endogenous_variables": "endogenousVariables",
            "left_censoring_limit": "leftCensoringLimit",
            "right_censoring_limit": "rightCensoringLimit",
        }
        self._execution_map = {
            OLSParams: self._execute_ols,
            BinaryChoiceRegressionParams: self._execute_binary_choice,
            TobitParams: self._execute_tobit,
            PanelDataParams: self._execute_panel,
            InstrumentalVariablesParams: self._execute_iv,
            RegularizedRegressionParams: self._execute_regularized,
        }

    def validate(self):
        # テーブル名の検証
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )

        # 列名リストの取得
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # スキーマの取得
        df_schema = self.tables_store.get_schema(self.table_name)

        # 説明変数の検証
        validate_existence(
            value=self.explanatory_variables,
            valid_list=column_name_list,
            target=self.param_names["explanatory_variables"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=self.explanatory_variables,
            target=self.param_names["explanatory_variables"],
        )

        # 被説明変数の検証
        validate_existence(
            value=self.dependent_variable,
            valid_list=column_name_list,
            target=self.param_names["dependent_variable"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=[self.dependent_variable],
            target=self.param_names["dependent_variable"],
        )

        # 分析手法ごとの追加検証
        match self.analysis:
            case PanelDataParams():
                # 固定効果分析の場合、個体IDと時間列の検証
                if self.analysis.entity_id_column:
                    validate_existence(
                        value=self.analysis.entity_id_column,
                        valid_list=column_name_list,
                        target=self.param_names["entity_id_column"],
                    )
                    validate_numeric_types(
                        schema=df_schema,
                        columns=self.analysis.entity_id_column,
                        target=self.param_names["entity_id_column"],
                    )
                if self.analysis.time_column:
                    validate_existence(
                        value=self.analysis.time_column,
                        valid_list=column_name_list,
                        target=self.param_names["time_column"],
                    )
                    validate_numeric_types(
                        schema=df_schema,
                        columns=self.analysis.time_column,
                        target=self.param_names["time_column"],
                    )
            case InstrumentalVariablesParams():
                # IV分析の場合、操作変数と内生変数の検証
                if self.analysis.instrumental_variables:
                    validate_existence(
                        value=self.analysis.instrumental_variables,
                        valid_list=column_name_list,
                        target=self.param_names["instrumental_variables"],
                    )
                    validate_numeric_types(
                        schema=df_schema,
                        columns=self.analysis.instrumental_variables,
                        target=self.param_names["instrumental_variables"],
                    )
                if self.analysis.endogenous_variables:
                    validate_existence(
                        value=self.analysis.endogenous_variables,
                        valid_list=column_name_list,
                        target=self.param_names["endogenous_variables"],
                    )
                    validate_numeric_types(
                        schema=df_schema,
                        columns=self.analysis.endogenous_variables,
                        target=self.param_names["endogenous_variables"],
                    )

    def execute(self):
        try:
            # テーブルの取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # データの準備
            y_data, x_data = prepare_basic_data(
                df,
                self.dependent_variable,
                self.explanatory_variables,
                self.has_const,
                MISSING_HANDLING_MAP.get(self.missing_value_handling, "drop"),
            )

            # 欠損値の処理を statsmodels の形式に変換
            missing = MISSING_HANDLING_MAP.get(
                self.missing_value_handling, "drop"
            )

            # モデルのフィット
            analysis_type = type(self.analysis)
            if analysis_type not in self._execution_map:
                raise NotImplementedError(
                    _("Specified regression method is not supported")
                )

            execute_method = self._execution_map[analysis_type]
            analysis_result = execute_method(
                df=df, y_data=y_data, x_data=x_data, missing=missing
            )

            # 分析結果をストアに保存
            analysis_result = AnalysisResult(
                name=self.result_name or self.dependent_variable,
                description=self.description,
                table_name=self.table_name,
                regression_output=analysis_result,
            )

            result_id = self.result_store.save_result(analysis_result)

            result = {
                "resultId": result_id,
            }
            # IDのみを返却
            return result
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=f"Unexpected error: {str(e)}",
            ) from e

    def _execute_ols(self, *, df, y_data, x_data, missing):
        if not isinstance(self.analysis, OLSParams):
            raise ValueError(
                _("Invalid analysis parameters for OLS regression")
            )
        model_result = fit_ols(y_data, x_data, missing)
        model_result = apply_standard_errors(
            model_result,
            self.standard_error,
        )
        return self._format_result(model_result)

    def _execute_binary_choice(self, *, df, y_data, x_data, missing):
        if not isinstance(self.analysis, BinaryChoiceRegressionParams):
            raise ValueError(
                _("Invalid analysis parameters for binary choice regression")
            )
        if self.analysis.method == RegressionMethodType.LOGIT:
            model_result = fit_logit(y_data, x_data, missing)
        elif self.analysis.method == RegressionMethodType.PROBIT:
            model_result = fit_probit(y_data, x_data, missing)
        else:
            raise NotImplementedError(
                _("Specified regression method is not supported")
            )

        model_result = apply_standard_errors(
            model_result,
            self.standard_error,
        )
        return self._format_result(model_result)

    def _execute_tobit(self, *, df, y_data, x_data, missing):
        if not isinstance(self.analysis, TobitParams):
            raise ValueError(
                _("Invalid analysis parameters for Tobit regression")
            )
        df_pandas = prepare_tobit_dataframe(
            df,
            self.dependent_variable,
            self.explanatory_variables,
            missing,
        )
        data_input = TobitInput(
            df_pandas=df_pandas,
            dependent_variable=self.dependent_variable,
            explanatory_variables=self.explanatory_variables,
            has_const=self.has_const,
            left_censoring_limit=self.analysis.left_censoring_limit,
            right_censoring_limit=self.analysis.right_censoring_limit,
        )
        model_result = fit_tobit(data_input)
        return self._tobit_format_result(
            model_result,
            self.analysis.left_censoring_limit,
            self.analysis.right_censoring_limit,
        )

    def _execute_panel(self, *, df, y_data, x_data, missing):
        if not isinstance(self.analysis, PanelDataParams):
            raise ValueError(
                _("Invalid analysis parameters for panel data regression")
            )
        panel_data_config = PanelDataConfig(
            dependent_variable=self.dependent_variable,
            explanatory_variables=self.explanatory_variables,
            entity_id_column=self.analysis.entity_id_column,
            time_column=self.analysis.time_column,
            missing=missing,
        )
        df_pandas = prepare_panel_dataframe(
            df,
            panel_data_config,
        )
        if self.analysis.method == RegressionMethodType.FE:
            model_result = fit_fe(
                df_pandas,
                self.dependent_variable,
                self.explanatory_variables,
                self.standard_error.method,
            )
            return self._fe_format_result(
                model_result, self.analysis.entity_id_column
            )
        elif self.analysis.method == RegressionMethodType.RE:
            model_result = fit_re(
                df_pandas,
                self.dependent_variable,
                self.explanatory_variables,
                self.standard_error.method,
            )
            return self._re_format_result(
                model_result, self.analysis.entity_id_column
            )
        else:
            raise NotImplementedError(
                _("Specified regression method is not supported")
            )

    def _execute_iv(self, *, df, y_data, x_data, missing):
        if not isinstance(self.analysis, InstrumentalVariablesParams):
            raise ValueError(
                _("Invalid analysis parameters for IV regression")
            )

        iv_data_config = IvDataConfig(
            dependent_variable=self.dependent_variable,
            explanatory_variables=self.explanatory_variables,
            endogenous_variables=self.analysis.endogenous_variables,
            instrumental_variables=self.analysis.instrumental_variables,
            missing=missing,
        )
        df_pandas = prepare_iv_dataframe(
            df,
            iv_data_config,
        )
        data_input = IVInput(
            df_pandas=df_pandas,
            dependent_variable=self.dependent_variable,
            explanatory_variables=self.explanatory_variables,
            endogenous_variables=self.analysis.endogenous_variables,
            instrumental_variables=self.analysis.instrumental_variables,
            standard_error_method=self.standard_error.method,
            has_const=self.has_const,
        )
        model_result = fit_iv(data_input)
        model_result = apply_standard_errors(
            model_result,
            self.standard_error,
        )
        return self._iv_format_result(
            model_result,
            self.analysis.endogenous_variables,
            self.analysis.instrumental_variables,
        )

    def _execute_regularized(self, *, df, y_data, x_data, missing):
        if not isinstance(self.analysis, RegularizedRegressionParams):
            raise ValueError(
                _("Invalid analysis parameters for regularized regression")
            )
        alpha = self.analysis.alpha
        calculate_se = self.analysis.calculate_se
        bootstrap_iterations = self.analysis.bootstrap_iterations

        data_input = RegularizedRegressionInput(
            y_data=y_data,
            x_data=x_data,
            has_const=self.has_const,
            alpha=alpha,
            missing=missing,
            calculate_se=calculate_se,
            bootstrap_iterations=bootstrap_iterations,
        )

        if self.analysis.method == RegressionMethodType.LASSO:
            model_result, coef_scaled = fit_lasso(data_input)
        elif self.analysis.method == RegressionMethodType.RIDGE:
            model_result, coef_scaled = fit_ridge(data_input)
        else:
            raise NotImplementedError(
                _("Specified regression method is not supported")
            )

        return self._format_regularized_result(model_result, coef_scaled)

    def _format_result(self, model_result: Any) -> dict:
        """
        分析結果を JSON 形式にフォーマット

        Args:
            model_result: statsmodels の回帰結果オブジェクト

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = model_result.summary().as_text()

        # パラメータの詳細情報
        param_names = (
            ["const"] if self.has_const else []
        ) + self.explanatory_variables
        params_info = extract_statsmodels_params(model_result, param_names)

        # モデル統計情報
        model_stats: dict[str, Any] = {"nObservations": int(model_result.nobs)}

        # 線形モデルの統計量
        if hasattr(model_result, "rsquared"):
            model_stats["R2"] = float(model_result.rsquared)
        if hasattr(model_result, "rsquared_adj"):
            model_stats["adjustedR2"] = float(model_result.rsquared_adj)
        if hasattr(model_result, "fvalue"):
            model_stats["fValue"] = float(model_result.fvalue)
        if hasattr(model_result, "f_pvalue"):
            model_stats["fProbability"] = float(model_result.f_pvalue)

        # 共通の統計量
        if hasattr(model_result, "aic"):
            model_stats["AIC"] = float(model_result.aic)
        if hasattr(model_result, "bic"):
            model_stats["BIC"] = float(model_result.bic)
        if hasattr(model_result, "llf"):
            model_stats["logLikelihood"] = float(model_result.llf)

        # 離散選択モデルの統計量
        if hasattr(model_result, "prsquared"):
            model_stats["pseudoRSquared"] = float(model_result.prsquared)

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
        }

        return result

    def _format_regularized_result(
        self, model_result: Any, coef_scaled: Any
    ) -> dict:
        """
        正則化回帰（Lasso/Ridge）の結果をJSON形式にフォーマット

        元のスケールの係数に加えて、標準化後の係数も返す。
        標準化後の係数は変数間の相対的重要度の比較に使用できる。

        Args:
            model_result: statsmodels の回帰結果オブジェクト
            coef_scaled: 標準化後の係数配列

        Returns:
            フォーマット済みの結果辞書
        """
        # 基本的なフォーマットを取得
        result = self._format_result(model_result)

        # 各パラメータに標準化後の係数を追加
        for i, param in enumerate(result["parameters"]):
            if param["variable"] == "const":
                # 定数項は標準化しないのでNone
                param["coefficientScaled"] = None
            else:
                # 定数項を除いたインデックス
                idx = i - 1 if self.has_const else i
                param["coefficientScaled"] = float(coef_scaled[idx])

        return result

    def _tobit_format_result(
        self, model_result, left_censoring_limit, right_censoring_limit
    ) -> dict:
        """
        Tobit モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: py4etrics の Tobit 回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary())

        # パラメータの詳細情報
        param_names = (
            ["const"] if self.has_const else []
        ) + self.explanatory_variables
        params_info = extract_statsmodels_params(model_result, param_names)

        # モデル統計情報
        model_stats: dict[str, Any] = {
            "nObservations": int(model_result.nobs),
            "logLikelihood": float(model_result.llf),
        }

        # AIC, BIC があれば追加
        if hasattr(model_result, "aic"):
            model_stats["AIC"] = float(model_result.aic)
        if hasattr(model_result, "bic"):
            model_stats["BIC"] = float(model_result.bic)

        # 診断結果 (diagnostics)
        diagnostics: dict[str, Any] = {
            "censoringLimits": {
                "left": left_censoring_limit,
                "right": right_censoring_limit,
            }
        }

        # sigma (誤差項の標準偏差)
        if hasattr(model_result, "scale"):
            diagnostics["sigma"] = float(model_result.scale)
            diagnostics["sigmaDescription"] = (
                "Standard error of the error term"
            )

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
            "diagnostics": diagnostics,
        }

        return result

    def _iv_format_result(
        self, model_result, endogenous_variables, instrumental_variables
    ) -> dict:
        """
        IV モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: linearmodels の回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary)

        # パラメータの詳細情報
        all_vars = self.explanatory_variables + endogenous_variables
        params_info = extract_linearmodels_params(model_result, all_vars)

        # モデル統計情報
        model_stats: dict[str, Any] = {
            "nObservations": int(model_result.nobs),
            "R2": float(model_result.rsquared),
        }

        # 診断結果 (diagnostics)
        diagnostics: dict[str, Any] = {}

        # 内生性の検定 (Wu-Hausman test)
        if hasattr(model_result, "wu_hausman"):
            try:
                wu_test = model_result.wu_hausman()
                diagnostics["wuHausmanTest"] = {
                    "statistic": float(wu_test.stat),
                    "pValue": float(wu_test.pval),
                    "description": "Test for endogeneity",
                }
            except Exception:
                pass

        # 過剰識別制約の検定 (Sargan/Hansen J test)
        if hasattr(model_result, "sargan"):
            try:
                sargan = model_result.sargan()
                diagnostics["sarganTest"] = {
                    "statistic": float(sargan.stat),
                    "pValue": float(sargan.pval),
                    "description": "Test for overidentifying restrictions",
                }
            except Exception:
                pass

        # 弱操作変数の検定 (First-stage F-statistic)
        if hasattr(model_result, "first_stage"):
            try:
                first_stage = model_result.first_stage
                diagnostics["firstStage"] = {}
                for endog_var in endogenous_variables:
                    if endog_var in first_stage.individual:
                        fs_result = first_stage.individual[endog_var]
                        diagnostics["firstStage"][endog_var] = {
                            "fStatistic": float(fs_result.f_stat.stat),
                            "pValue": float(fs_result.f_stat.pval),
                            "description": "First-stage F-test for "
                            "weak instruments",
                        }
            except Exception:
                pass

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "endogenousVariables": endogenous_variables,
            "instrumentalVariables": instrumental_variables,
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
            "diagnostics": diagnostics,
        }

        return result

    def _fe_format_result(self, model_result, entity_id_column) -> dict:
        """
        固定効果モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: linearmodels の回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary)

        # パラメータの詳細情報
        params_info = extract_linearmodels_params(
            model_result, self.explanatory_variables
        )

        # モデル統計情報と診断結果
        model_stats: dict[str, Any] = {
            "nObservations": int(model_result.nobs),
            "nEntities": int(model_result.entity_info["total"]),
            "R2Within": float(model_result.rsquared),
            "R2Between": float(model_result.rsquared_between),
            "R2Overall": float(model_result.rsquared_overall),
            "fValue": float(model_result.f_statistic.stat),
            "fProbability": float(model_result.f_statistic.pval),
        }

        # 診断結果 (diagnostics)
        diagnostics: dict[str, Any] = {
            "rsquaredWithin": float(model_result.rsquared),
            "rsquaredBetween": float(model_result.rsquared_between),
            "rsquaredOverall": float(model_result.rsquared_overall),
        }

        # 個体効果の有意性検定 (F-test for pooled model)
        if hasattr(model_result, "f_pooled"):
            diagnostics["fPooled"] = {
                "statistic": float(model_result.f_pooled.stat),
                "pValue": float(model_result.f_pooled.pval),
                "description": "Test for entity effects",
            }

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "entityIdColumn": entity_id_column,
            "estimationMethod": "Fixed Effects (Within)",
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
            "diagnostics": diagnostics,
        }

        return result

    def _re_format_result(self, model_result, entity_id_column) -> dict:
        """
        変量効果モデルの結果を JSON 形式にフォーマット

        Args:
            model_result: linearmodels の回帰結果

        Returns:
            フォーマット済みの結果辞書
        """
        summary_text = str(model_result.summary)

        # パラメータの詳細情報
        params_info = extract_linearmodels_params(
            model_result, self.explanatory_variables
        )

        # モデル統計情報と診断結果
        model_stats: dict[str, Any] = {
            "nObservations": int(model_result.nobs),
            "R2Within": float(model_result.rsquared),
            "R2Between": float(model_result.rsquared_between),
            "R2Overall": float(model_result.rsquared_overall),
        }

        # 診断結果 (diagnostics)
        diagnostics: dict[str, Any] = {
            "rsquaredWithin": float(model_result.rsquared),
            "rsquaredBetween": float(model_result.rsquared_between),
            "rsquaredOverall": float(model_result.rsquared_overall),
        }

        # theta (変量効果の重み)
        if hasattr(model_result, "theta"):
            theta_value = model_result.theta
            # thetaがDataFrameの場合は平均値を取る
            if hasattr(theta_value, "mean"):
                if hasattr(theta_value, "values"):
                    # DataFrameまたはSeriesの場合
                    diagnostics["theta"] = float(theta_value.values.mean())
                else:
                    diagnostics["theta"] = float(theta_value.mean())
            else:
                diagnostics["theta"] = float(theta_value)
            diagnostics["thetaDescription"] = (
                "Weight of random effects transformation (0=pooled, 1=within)"
            )

        result = {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "entityIdColumn": entity_id_column,
            "estimationMethod": "Random Effects (GLS)",
            "regressionResult": summary_text,
            "parameters": params_info,
            "modelStatistics": model_stats,
            "diagnostics": diagnostics,
        }

        return result

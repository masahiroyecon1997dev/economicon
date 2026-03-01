import logging
from typing import Any, ClassVar

import numpy as np
from scipy import stats as spstats

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import (
    BinaryChoiceRegressionParams,
    ClusteredStandardError,
    InstrumentalVariablesParams,
    OLSParams,
    PanelDataParams,
    PanelIvParams,
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
    RegularizedResult,
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
    fit_tobit_null,
)
from economicon.services.regressions.standard_errors import (
    apply_standard_errors,
)
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_numeric_types,
)

_logger = logging.getLogger(__name__)


class Regression:
    """
    回帰分析を実行するためのAPIクラス

    指定された分析タイプに基づいて、適切な回帰分析を実行します。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
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

        self._execution_map = {
            OLSParams: self._execute_ols,
            BinaryChoiceRegressionParams: self._execute_binary_choice,
            TobitParams: self._execute_tobit,
            PanelDataParams: self._execute_panel,
            InstrumentalVariablesParams: self._execute_iv,
            RegularizedRegressionParams: self._execute_regularized,
            PanelIvParams: self._execute_panel_iv,
        }

    def validate(self):
        # テーブル名の検証
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
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
            target=self.PARAM_NAMES["explanatory_variables"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=self.explanatory_variables,
            target=self.PARAM_NAMES["explanatory_variables"],
        )

        # 被説明変数の検証
        validate_existence(
            value=self.dependent_variable,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["dependent_variable"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=[self.dependent_variable],
            target=self.PARAM_NAMES["dependent_variable"],
        )

        # 分析手法ごとの追加検証
        match self.analysis:
            case PanelDataParams():
                # 固定効果分析の場合、個体IDと時間列の検証
                if self.analysis.entity_id_column:
                    validate_existence(
                        value=self.analysis.entity_id_column,
                        valid_list=column_name_list,
                        target=self.PARAM_NAMES["entity_id_column"],
                    )
                    validate_numeric_types(
                        schema=df_schema,
                        columns=self.analysis.entity_id_column,
                        target=self.PARAM_NAMES["entity_id_column"],
                    )
                if self.analysis.time_column:
                    validate_existence(
                        value=self.analysis.time_column,
                        valid_list=column_name_list,
                        target=self.PARAM_NAMES["time_column"],
                    )
                    validate_numeric_types(
                        schema=df_schema,
                        columns=self.analysis.time_column,
                        target=self.PARAM_NAMES["time_column"],
                    )
            case InstrumentalVariablesParams():
                # IV分析の場合、操作変数と内生変数の検証
                if self.analysis.instrumental_variables:
                    validate_existence(
                        value=self.analysis.instrumental_variables,
                        valid_list=column_name_list,
                        target=self.PARAM_NAMES["instrumental_variables"],
                    )
                    validate_numeric_types(
                        schema=df_schema,
                        columns=self.analysis.instrumental_variables,
                        target=self.PARAM_NAMES["instrumental_variables"],
                    )
                if self.analysis.endogenous_variables:
                    validate_existence(
                        value=self.analysis.endogenous_variables,
                        valid_list=column_name_list,
                        target=self.PARAM_NAMES["endogenous_variables"],
                    )
                    validate_numeric_types(
                        schema=df_schema,
                        columns=self.analysis.endogenous_variables,
                        target=self.PARAM_NAMES["endogenous_variables"],
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

            # raw モデル情報を格納するインスタンス変数を初期化
            # （各 _execute_* メソッド内でセットされる）
            self._last_raw_model: Any = None
            self._last_model_type: str | None = None
            self._last_entity_id_column: str | None = None
            self._last_time_column: str | None = None
            # Critical#3: Tobit の欠損除去後の行インデックス
            # (診断列追加時の行ズレ防止用)
            self._last_row_indices: np.ndarray | None = None

            execute_method = self._execution_map[analysis_type]
            regression_output = execute_method(
                df=df, y_data=y_data, x_data=x_data, missing=missing
            )

            # 分析結果をストアに保存
            analysis_result = AnalysisResult(
                name=self.result_name or self.dependent_variable,
                description=self.description,
                table_name=self.table_name,
                regression_output=regression_output,
                model_type=self._last_model_type,
                entity_id_column=self._last_entity_id_column,
                time_column=self._last_time_column,
                row_indices=self._last_row_indices,
            )

            result_id = self.result_store.save_result(analysis_result)

            # pickle でモデルをファイルに保存（メモリ節約のため直後に解放）
            if self._last_raw_model is not None:
                analysis_result.save_model(self._last_raw_model)
                del self._last_raw_model
                self._last_raw_model = None

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
            groups_arrays=self._build_groups_arrays(
                df=df, y_data=y_data, x_data=x_data
            ),
        )
        self._last_raw_model = model_result
        self._last_model_type = "ols"
        return self._format_result(model_result)

    def _execute_binary_choice(self, *, df, y_data, x_data, missing):
        if not isinstance(self.analysis, BinaryChoiceRegressionParams):
            raise ValueError(
                _("Invalid analysis parameters for binary choice regression")
            )
        if self.analysis.method == RegressionMethodType.LOGIT:
            model_result = fit_logit(y_data, x_data, missing)
            self._last_model_type = "logit"
        elif self.analysis.method == RegressionMethodType.PROBIT:
            model_result = fit_probit(y_data, x_data, missing)
            self._last_model_type = "probit"
        else:
            raise NotImplementedError(
                _("Specified regression method is not supported")
            )

        model_result = apply_standard_errors(
            model_result,
            self.standard_error,
            groups_arrays=self._build_groups_arrays(
                df=df, y_data=y_data, x_data=x_data
            ),
        )
        self._last_raw_model = model_result
        result = self._format_result(model_result)
        # 平均限界効果 (AME) の計算
        if self.analysis.calculate_marginal_effects:
            result["marginalEffects"] = self._compute_ame(model_result)
        return result

    def _build_groups_arrays(
        self, *, df: Any, y_data: Any, x_data: Any
    ) -> dict[str, Any] | None:
        """
        ClusteredStandardError 用の欠邺除去済みグループ配列辞書を構築する。

        statsmodels の欠邺値除去マスク（yまたはxに NaN を含む行を除去）
        と同一のマスクを当て、列名 → numpy 配列の辞書を返す。
        ClusteredStandardError 以外の場合は None を返す。

        Args:
            df: Polars DataFrame（型刧を含む）
            y_data: 被説明変数の numpy 配列
            x_data: 説明変数の numpy 配列（多次元または 1 次元）

        Returns:
            {``列名``: numpy 配列} 辞書、または None
        """
        if not isinstance(self.standard_error, ClusteredStandardError):
            return None
        x_nan = (
            np.isnan(x_data).any(axis=1)
            if x_data.ndim > 1
            else np.isnan(x_data)
        )
        valid_mask = ~(np.isnan(y_data) | x_nan)
        return {
            col: df[col].to_numpy()[valid_mask]
            for col in self.standard_error.groups
        }

    def _compute_ame(self, model_result: Any) -> list[dict[str, Any]]:
        """
        平均限界効果 (Average Marginal Effects, AME) を計算

        at='overall' でデータ全体の平均を使用する。
        定数項は結果から除外する（解釈不能なため）。

        Args:
            model_result: apply_standard_errors 適用後の
                statsmodels 回帰結果

        Returns:
            各説明変数の AME 情報辞書のリスト
        """
        try:
            margeff = model_result.get_margeff(at="overall")
            param_names = (
                ["const"] if self.has_const else []
            ) + self.explanatory_variables
            ci = margeff.conf_int()
            result_list: list[dict[str, Any]] = []
            # Critical#1: margeff の下標は定数項を含まないため
            # param_names とは別に ame_idx で管理する。
            # loop index i をそのまま使うと定数項スキップ時に 1 ずれる。
            ame_idx = 0
            for name in param_names:
                if name == "const":
                    continue  # 定数項は AME に含めない
                result_list.append(
                    {
                        "variable": name,
                        "marginalEffect": float(margeff.margeff[ame_idx]),
                        "standardError": float(margeff.margeff_se[ame_idx]),
                        "tValue": float(margeff.tvalues[ame_idx]),
                        "pValue": float(margeff.pvalues[ame_idx]),
                        "confidenceIntervalLower": float(ci[ame_idx, 0]),
                        "confidenceIntervalUpper": float(ci[ame_idx, 1]),
                    }
                )
                ame_idx += 1
            return result_list
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
                message=_("Failed to compute average marginal effects"),
            ) from e

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
        # Critical#3: dropna() 後の pandas インデックスを保存
        # 診断列追加時の行ズレを防止する
        self._last_row_indices = df_pandas.index.to_numpy(dtype=np.int64)
        data_input = TobitInput(
            df_pandas=df_pandas,
            dependent_variable=self.dependent_variable,
            explanatory_variables=self.explanatory_variables,
            has_const=self.has_const,
            left_censoring_limit=self.analysis.left_censoring_limit,
            right_censoring_limit=self.analysis.right_censoring_limit,
        )
        model_result = fit_tobit(data_input)
        # LR 検定: 定数項のみのモデルと比較
        lr_test_result: dict[str, Any] | None = None
        try:
            null_result = fit_tobit_null(data_input)
            n_slopes = len(self.explanatory_variables)
            lr_stat = 2.0 * (float(model_result.llf) - float(null_result.llf))
            lr_pvalue = float(spstats.chi2.sf(lr_stat, df=n_slopes))
            lr_test_result = {
                "statistic": lr_stat,
                "pValue": lr_pvalue,
                "df": n_slopes,
                "description": (
                    "Likelihood ratio test vs. constant-only Tobit"
                ),
            }
        except Exception as _lr_exc:
            # Warning#9: LR 検定失敗をサイレントに
            # 無視するのではなくログに記録する
            _logger.warning("Tobit LR test failed: %s", _lr_exc)
        self._last_raw_model = model_result
        self._last_model_type = "tobit"
        return self._tobit_format_result(
            model_result,
            self.analysis.left_censoring_limit,
            self.analysis.right_censoring_limit,
            lr_test_result=lr_test_result,
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
            self._last_raw_model = model_result
            self._last_model_type = "fe"
            self._last_entity_id_column = self.analysis.entity_id_column
            self._last_time_column = self.analysis.time_column
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
            self._last_raw_model = model_result
            self._last_model_type = "re"
            self._last_entity_id_column = self.analysis.entity_id_column
            self._last_time_column = self.analysis.time_column
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
            iv_method=self.analysis.iv_method,
            gmm_weight_matrix=self.analysis.gmm_weight_matrix,
        )
        model_result = fit_iv(data_input)
        self._last_raw_model = model_result
        self._last_model_type = "iv"
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
        # Eco-Note C: random_state を渡してブートストラップの再現性を確保
        random_state = self.analysis.random_state

        data_input = RegularizedRegressionInput(
            y_data=y_data,
            x_data=x_data,
            has_const=self.has_const,
            alpha=alpha,
            missing=missing,
            calculate_se=calculate_se,
            bootstrap_iterations=bootstrap_iterations,
            random_state=random_state,
        )

        if self.analysis.method == RegressionMethodType.LASSO:
            reg_result = fit_lasso(data_input)
            self._last_model_type = "lasso"
        elif self.analysis.method == RegressionMethodType.RIDGE:
            reg_result = fit_ridge(data_input)
            self._last_model_type = "ridge"
        else:
            raise NotImplementedError(
                _("Specified regression method is not supported")
            )

        self._last_raw_model = reg_result
        return self._format_regularized_result(reg_result)

    def _execute_panel_iv(self, *, df, y_data, x_data, missing):
        raise NotImplementedError(
            _("Specified regression method is not supported")
        )

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
        self, reg_result: RegularizedResult
    ) -> dict:
        """
        正則化回帰（Lasso/Ridge）の結果を JSON 形式にフォーマット

        - R²: 訓練データでの sklearn model.score()
        - adjustedR2, fValue, fProbability, tValue, pValue: None
          （正則化回帰には理論的根拠なし）
        - Ridge: bootstrapSE + 95% パーセンタイル CI
        - Lasso: selectionRate + 95% パーセンタイル CI、SE は None
          （点質量問題により過小評価されるため）

        Args:
            reg_result: RegularizedResult データクラス

        Returns:
            フォーマット済みの結果辞書
        """
        param_names = (
            ["const"] if reg_result.has_const else []
        ) + self.explanatory_variables

        params_info: list[dict[str, Any]] = []
        for i, name in enumerate(param_names):
            is_const = name == "const"
            # coef_scaled / selection_rate の添字
            # （定数項を除く n_features 次元）
            var_idx = (i - 1) if reg_result.has_const else i

            param_dict: dict[str, Any] = {
                "variable": name,
                "coefficient": float(reg_result.params_original[i]),
                "coefficientScaled": (
                    None
                    if is_const
                    else float(reg_result.coef_scaled[var_idx])
                ),
                # Ridge: bootstrap 標準偏差、Lasso: None
                "standardError": (
                    None
                    if (reg_result.bootstrap_se is None or is_const)
                    else float(reg_result.bootstrap_se[i])
                ),
                # 正則化回帰では t/p 値は無意味
                "tValue": None,
                "pValue": None,
                # calculate_se=True 時: パーセンタイル法 95% CI
                "confidenceIntervalLower": (
                    None
                    if reg_result.bootstrap_ci_lower is None
                    else float(reg_result.bootstrap_ci_lower[i])
                ),
                "confidenceIntervalUpper": (
                    None
                    if reg_result.bootstrap_ci_upper is None
                    else float(reg_result.bootstrap_ci_upper[i])
                ),
            }

            # Lasso のみ: 選択率（定数項を除く）
            if reg_result.selection_rate is not None and not is_const:
                param_dict["selectionRate"] = float(
                    reg_result.selection_rate[var_idx]
                )

            params_info.append(param_dict)

        model_stats: dict[str, Any] = {
            "nObservations": reg_result.n_obs,
            "R2": reg_result.r2,
            "adjustedR2": None,
            "fValue": None,
            "fProbability": None,
        }

        return {
            "tableName": self.table_name,
            "dependentVariable": self.dependent_variable,
            "explanatoryVariables": self.explanatory_variables,
            "regressionResult": None,
            "parameters": params_info,
            "modelStatistics": model_stats,
        }

    def _tobit_format_result(
        self,
        model_result,
        left_censoring_limit,
        right_censoring_limit,
        *,
        lr_test_result: dict[str, Any] | None = None,
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

        # Wald 検定: 全傾斜係数の同時有意性
        try:
            n_params = len(model_result.params)
            start_idx = 1 if self.has_const else 0
            n_slopes = n_params - start_idx
            if n_slopes > 0:
                # 制約行列 R: 全傾斜係数を選択（計量経済では R と表記）
                r_matrix = np.eye(n_params)[start_idx:]
                # scalar=True: 将来のデフォルト動作を明示的に採用
                wald = model_result.wald_test(r_matrix, scalar=True)
                diagnostics["waldTest"] = {
                    "statistic": float(wald.statistic),
                    "pValue": float(wald.pvalue),
                    "df": n_slopes,
                    "description": (
                        "Wald test for joint significance of slope parameters"
                    ),
                }
        except Exception:
            pass

        # LR 検定: 定数項のみのモデルと比較
        if lr_test_result is not None:
            diagnostics["lrTest"] = lr_test_result

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
        # 注意: linearmodels は has_const=True 時に const を自動追加するため
        #       param_names にも const を含める必要がある
        all_vars = (
            (["const"] if self.has_const else [])
            + self.explanatory_variables
            + endogenous_variables
        )
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
        # sargan は呼び出し可能メソッドではなく WaldTestStatistic プロパティ
        if hasattr(model_result, "sargan"):
            try:
                sargan = model_result.sargan
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
                            # OLSResults の属性は f_statistic
                            # (f_stat は存在しないため AttributeError になる)
                            "fStatistic": float(fs_result.f_statistic.stat),
                            "pValue": float(fs_result.f_statistic.pval),
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
        diagnostics: dict[str, Any] = {}

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
        diagnostics: dict[str, Any] = {}

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

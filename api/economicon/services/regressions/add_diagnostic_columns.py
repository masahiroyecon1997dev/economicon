"""
推定モデルからの予測値・残差抽出および Polars テーブルへの統合

シリアライズ保存された推定モデルを読み込み、選択されたパラメータに基づき
予測値・残差を計算して元の Polars DataFrame に新しい列として追加・保存する。
"""

import gc
from typing import ClassVar, Literal

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models.regressions import AddDiagnosticColumnsRequestBody
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from economicon.services.regressions.diagnostics import (
    DiagnosticExtractOptions,
    PanelExtractConfig,
    TobitExtractConfig,
    extract_from_linearmodels_iv,
    extract_from_linearmodels_panel,
    extract_from_regularized,
    extract_from_statsmodels,
    extract_from_tobit,
)
from economicon.services.regressions.fitters import RegularizedResult
from economicon.utils import ProcessingError, ValidationError
from economicon.utils.validators import validate_existence


class AddDiagnosticColumns:
    """
    推定済みモデルから予測値・残差を抽出してテーブルに追加するサービス

    DataOperation Protocol 準拠。

    処理フロー
    ----------
    1. validate(): テーブル・結果 ID・pkl ファイルの存在確認
    2. execute():
       a. AnalysisResultStore から AnalysisResult を取得
       b. AnalysisResult.load_model() で pkl からモデルをロード
       c. model_type に応じた extract_from_* 関数を呼び出し
       d. 元テーブルと left_join（行の整合性を完全に保つ）
       e. TablesStore.update_table() で保存
       f. raw モデルを即座に解放（メモリ節約）
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "result_id": "resultId",
        "entity_id_column": "entityIdColumn",
        "time_column": "timeColumn",
    }

    # OLS / Logit / Probit の statsmodels 系モデルタイプ（Tobit は別分岐）
    _STATSMODELS_TYPES = frozenset({"ols", "logit", "probit"})
    # 正則化回帰（statsmodels Lasso/Ridge）
    _REGULARIZED_TYPES = frozenset({"ridge", "lasso"})

    def __init__(
        self,
        body: AddDiagnosticColumnsRequestBody,
        tables_store: TablesStore,
        result_store: AnalysisResultStore,
    ):
        self.tables_store = tables_store
        self.result_store = result_store
        self.table_name = body.table_name
        self.result_id = body.result_id
        self.target: Literal["fitted", "residual", "both"] = body.target
        self.standardized = body.standardized
        self.include_interval = body.include_interval
        self.fe_type: Literal["total", "within"] = body.fe_type
        # Eco-Note A: Logit/Probit の残差種別
        self.binary_residual_type: Literal["raw", "deviance"] = (
            body.binary_residual_type
        )
        # Eco-Note B: Tobit の予測値種別
        self.tobit_fitted_type: Literal["latent", "observable"] = (
            body.tobit_fitted_type
        )

    # ------------------------------------------------------------------
    # バリデーション
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        入力値の事前検証

        Raises
        ------
        ValidationError
            - テーブルが存在しない場合
            - result_id が存在しない場合
            - pkl ファイルが見つからない場合
            - FE/RE モデルで entity_id_column / time_column が
              テーブルに存在しない場合
        """
        # テーブル名の存在確認
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )

        # result_id の存在確認
        try:
            analysis_result = self.result_store.get_result(self.result_id)
        except KeyError:
            raise ValidationError(
                error_code=ErrorCode.DATA_NOT_FOUND,
                message=_("Analysis result not found: resultId = %(id)s")
                % {"id": self.result_id},
            ) from None

        # pkl ファイルの存在確認
        if not analysis_result.has_model_file():
            raise ValidationError(
                error_code=ErrorCode.MODEL_FILE_NOT_FOUND,
                message=_("Model file not found for result: resultId = %(id)s")
                % {"id": self.result_id},
            )

        # FE/RE の場合、entity_id_column / time_column をテーブルで確認
        model_type = analysis_result.model_type
        if model_type in ("fe", "re"):
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            entity_col = analysis_result.entity_id_column
            time_col = analysis_result.time_column
            if entity_col and entity_col not in column_name_list:
                raise ValidationError(
                    error_code=ErrorCode.MODEL_KEY_MISMATCH,
                    message=_(
                        "Entity ID column '%(col)s' not found in table "
                        "'%(table)s'"
                    )
                    % {"col": entity_col, "table": self.table_name},
                )
            if time_col and time_col not in column_name_list:
                raise ValidationError(
                    error_code=ErrorCode.MODEL_KEY_MISMATCH,
                    message=_(
                        "Time column '%(col)s' not found in table '%(table)s'"
                    )
                    % {"col": time_col, "table": self.table_name},
                )

    # ------------------------------------------------------------------
    # 実行
    # ------------------------------------------------------------------

    def execute(self) -> dict:
        """
        モデルから診断値を抽出してテーブルに列追加する

        Returns
        -------
        dict
            追加したテーブル名と列名リストを含む辞書

        Raises
        ------
        ProcessingError
            予期しないエラーが発生した場合
        """
        try:
            analysis_result = self.result_store.get_result(self.result_id)
            model_type = analysis_result.model_type

            if not model_type:
                raise ProcessingError(
                    error_code=ErrorCode.MODEL_TYPE_NOT_SUPPORTED,
                    message=_(
                        "Model type is not set for result: resultId = %(id)s"
                    )
                    % {"id": self.result_id},
                )

            # pkl からモデルをロード（処理後にすぐ解放）
            raw_model = analysis_result.load_model()

            try:
                table_info = self.tables_store.get_table(self.table_name)
                df = table_info.table
                existing_cols = df.columns

                # 分析結果の被説明変数名を接頭辞として取得
                dep_var = analysis_result.regression_output.get(
                    "dependentVariable", "y"
                )

                # モデル種別に応じたデータ抽出
                values_df, added_cols = self._dispatch_extract(
                    raw_model=raw_model,
                    model_type=model_type,
                    dep_var=dep_var,
                    existing_cols=existing_cols,
                    analysis_result=analysis_result,
                )

            finally:
                # メモリ節約：ロードしたモデルを即座に解放
                del raw_model
                gc.collect()

            if not added_cols:
                return {
                    "tableName": self.table_name,
                    "addedColumns": [],
                }

            # 元テーブルと結合
            joined_df = self._join_to_table(
                df=df,
                values_df=values_df,
                model_type=model_type,
                analysis_result=analysis_result,
                added_cols=added_cols,
            )

            # テーブルを更新して保存
            self.tables_store.update_table(self.table_name, joined_df)

            return {
                "tableName": self.table_name,
                "addedColumns": added_cols,
            }

        except ProcessingError, ValidationError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.ADD_DIAGNOSTIC_COLUMNS_PROCESS_ERROR,
                message=_(
                    "Unexpected error during adding diagnostic columns: "
                    "%(err)s"
                )
                % {"err": str(e)},
            ) from e

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    def _dispatch_extract(
        self,
        raw_model: object,
        model_type: str,
        dep_var: str,
        existing_cols: list[str],
        analysis_result: object,
    ) -> tuple[pl.DataFrame, list[str]]:
        """
        model_type に応じて適切な extract_from_* 関数を呼び出す

        Returns
        -------
        tuple[pl.DataFrame, list[str]]
            (値 DataFrame, 追加される列名リスト)
        """
        if model_type in self._STATSMODELS_TYPES:
            opts = DiagnosticExtractOptions(
                dep_var=dep_var,
                existing_cols=existing_cols,
                target=self.target,
                standardized=self.standardized,
                include_interval=self.include_interval,
            )
            return extract_from_statsmodels(
                model=raw_model,
                options=opts,
                # Eco-Note A: Logit/Probit 残差種別を渡す
                residual_type=self.binary_residual_type,
            )

        if model_type == "tobit":
            # Eco-Note B: 打ち切り値を regression_output から取得し
            # observable 期待値の計算に使用する
            _diag = analysis_result.regression_output.get("diagnostics", {})  # type: ignore[union-attr]
            _cens = (
                _diag.get("censoringLimits", {})
                if isinstance(_diag, dict)
                else {}
            )
            opts = DiagnosticExtractOptions(
                dep_var=dep_var,
                existing_cols=existing_cols,
                target=self.target,
            )
            tobit_cfg = TobitExtractConfig(
                row_indices=analysis_result.row_indices,  # type: ignore[union-attr]
                fitted_type=self.tobit_fitted_type,
                left_censoring_limit=_cens.get("left"),
                right_censoring_limit=_cens.get("right"),
            )
            return extract_from_tobit(
                model=raw_model,
                options=opts,
                tobit_config=tobit_cfg,
            )

        if model_type in ("fe", "re"):
            entity_col = analysis_result.entity_id_column  # type: ignore[union-attr]
            time_col = analysis_result.time_column  # type: ignore[union-attr]
            opts = DiagnosticExtractOptions(
                dep_var=dep_var,
                existing_cols=existing_cols,
                target=self.target,
                include_interval=self.include_interval,
            )
            panel_cfg = PanelExtractConfig(
                entity_id_column=entity_col,
                time_column=time_col,
                fe_type=self.fe_type,
            )
            return extract_from_linearmodels_panel(
                model=raw_model,
                options=opts,
                panel_config=panel_cfg,
            )

        if model_type == "iv":
            opts = DiagnosticExtractOptions(
                dep_var=dep_var,
                existing_cols=existing_cols,
                target=self.target,
                include_interval=self.include_interval,
            )
            return extract_from_linearmodels_iv(
                model=raw_model,
                options=opts,
            )

        if model_type in self._REGULARIZED_TYPES:
            if not isinstance(raw_model, RegularizedResult):
                raise ProcessingError(
                    error_code=ErrorCode.MODEL_TYPE_NOT_SUPPORTED,
                    message=_(
                        "Unexpected model object for regularized regression"
                    ),
                )
            opts = DiagnosticExtractOptions(
                dep_var=dep_var,
                existing_cols=existing_cols,
                target=self.target,
            )
            return extract_from_regularized(
                reg_result=raw_model,
                options=opts,
            )

        raise ProcessingError(
            error_code=ErrorCode.MODEL_TYPE_NOT_SUPPORTED,
            message=_("Unsupported model type: %(type)s")
            % {"type": model_type},
        )

    def _join_to_table(
        self,
        df: pl.DataFrame,
        values_df: pl.DataFrame,
        model_type: str,
        analysis_result: object,
        added_cols: list[str],
    ) -> pl.DataFrame:
        """
        元テーブルと診断値 DataFrame を left_join する。

        FE/RE は entity_id_column + time_column の 2 キー結合。
        それ以外は ``__row_idx__`` を一時キーとして結合。

        欠損値を含む行は join 結果が null になるが、
        これは元データに欠損があるためであり仕様どおり。

        Parameters
        ----------
        df:
            元の Polars DataFrame（更新前）。
        values_df:
            extract_from_* が返した診断値 DataFrame。
        model_type:
            モデルタイプ文字列。
        analysis_result:
            AnalysisResult オブジェクト（キー列名の取得用）。
        added_cols:
            追加する列名リスト。

        Returns
        -------
        pl.DataFrame
            診断列を追加した Polars DataFrame。
        """
        if model_type in ("fe", "re"):
            entity_col = analysis_result.entity_id_column  # type: ignore[union-attr]
            time_col = analysis_result.time_column  # type: ignore[union-attr]
            joined = df.join(
                values_df.select([entity_col, time_col] + added_cols),
                on=[entity_col, time_col],
                how="left",
            )
        else:
            # __row_idx__ を一時キーとして使用
            joined = (
                df.with_row_index("__row_idx__")
                .join(
                    values_df,
                    on="__row_idx__",
                    how="left",
                )
                .drop("__row_idx__")
            )

        return joined

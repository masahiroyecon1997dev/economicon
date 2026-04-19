"""
回帰分析共通バリデーション関数

各回帰モデルクラスから呼び出される純粋バリデーション関数群。
"""

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.entities import (
    FEParams,
    InstrumentalVariablesParams,
    PanelIvParams,
    REParams,
)
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_numeric_types,
)

_PARAM_NAMES: dict[str, str] = {
    "table_name": "tableName",
    "dependent_variable": "dependentVariable",
    "explanatory_variables": "explanatoryVariables",
    "entity_id_column": "entityIdColumn",
    "time_column": "timeColumn",
    "instrumental_variables": "instrumentalVariables",
    "endogenous_variables": "endogenousVariables",
}


def validate_base_params(
    table_name: str,
    dependent_variable: str,
    explanatory_variables: list[str],
    tables_store: TablesStore,
) -> tuple[list[str], pl.Schema]:
    """テーブル存在・列存在・数値型の共通バリデーション。

    Returns
    -------
    (column_name_list, df_schema)
        呼び出し側の追加バリデーションで再利用できるよう返す。
    """
    table_name_list = tables_store.get_table_name_list()
    validate_existence(
        value=table_name,
        valid_list=table_name_list,
        target=_PARAM_NAMES["table_name"],
    )

    column_name_list = tables_store.get_column_name_list(table_name)
    df_schema = tables_store.get_schema(table_name)

    validate_existence(
        value=explanatory_variables,
        valid_list=column_name_list,
        target=_PARAM_NAMES["explanatory_variables"],
    )
    validate_numeric_types(
        schema=df_schema,
        columns=explanatory_variables,
        target=_PARAM_NAMES["explanatory_variables"],
    )

    validate_existence(
        value=dependent_variable,
        valid_list=column_name_list,
        target=_PARAM_NAMES["dependent_variable"],
    )
    validate_numeric_types(
        schema=df_schema,
        columns=[dependent_variable],
        target=_PARAM_NAMES["dependent_variable"],
    )

    return column_name_list, df_schema


def validate_panel_columns(
    analysis: FEParams | REParams,
    column_name_list: list[str],
    df_schema: pl.Schema,
) -> None:
    """entity_id_column / time_column の存在・型チェック。"""
    if analysis.entity_id_column:
        validate_existence(
            value=analysis.entity_id_column,
            valid_list=column_name_list,
            target=_PARAM_NAMES["entity_id_column"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=analysis.entity_id_column,
            target=_PARAM_NAMES["entity_id_column"],
        )
    if analysis.time_column:
        validate_existence(
            value=analysis.time_column,
            valid_list=column_name_list,
            target=_PARAM_NAMES["time_column"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=analysis.time_column,
            target=_PARAM_NAMES["time_column"],
        )


def validate_iv_columns(
    analysis: InstrumentalVariablesParams,
    column_name_list: list[str],
    df_schema: pl.Schema,
) -> None:
    """instrumental_variables / endogenous_variables の存在・型チェック。"""
    if analysis.instrumental_variables:
        validate_existence(
            value=analysis.instrumental_variables,
            valid_list=column_name_list,
            target=_PARAM_NAMES["instrumental_variables"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=analysis.instrumental_variables,
            target=_PARAM_NAMES["instrumental_variables"],
        )
    if analysis.endogenous_variables:
        validate_existence(
            value=analysis.endogenous_variables,
            valid_list=column_name_list,
            target=_PARAM_NAMES["endogenous_variables"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=analysis.endogenous_variables,
            target=_PARAM_NAMES["endogenous_variables"],
        )


def validate_wls_weights(
    weights_column: str,
    column_name_list: list[str],
    df_schema: pl.Schema,
    tables_store: TablesStore,
    table_name: str,
) -> None:
    """weights_column の存在・数値型・全値 > 0 チェック。"""
    validate_existence(
        value=weights_column,
        valid_list=column_name_list,
        target="weightsColumn",
    )
    validate_numeric_types(
        schema=df_schema,
        columns=[weights_column],
        target="weightsColumn",
    )
    # 全値 > 0 チェック（Polars で検証）
    df = tables_store.get_table(table_name).table
    n_invalid = df.filter(
        pl.col(weights_column).is_null() | (pl.col(weights_column) <= 0)
    ).height
    if n_invalid > 0:
        raise ProcessingError(
            error_code=ErrorCode.INVALID_WEIGHTS_VALUES,
            message=_(
                "weightsColumn must contain only positive values (> 0)."
                " Found {} invalid values."
            ).format(n_invalid),
        )


def validate_gls_sigma(
    sigma_table_name: str,
    n_obs: int,
    tables_store: TablesStore,
) -> pl.DataFrame:
    """sigma テーブルの存在・正方性・次元一致チェック。

    Returns
    -------
    sigma テーブルの Polars DataFrame
    """
    table_name_list = tables_store.get_table_name_list()
    validate_existence(
        value=sigma_table_name,
        valid_list=table_name_list,
        target="sigmaTableName",
    )
    sigma_df = tables_store.get_table(sigma_table_name).table
    n_rows, n_cols = sigma_df.height, len(sigma_df.columns)
    if n_rows != n_cols or n_rows != n_obs:
        raise ProcessingError(
            error_code=ErrorCode.SIGMA_DIMENSION_MISMATCH,
            message=_(
                "sigmaTableName must be a {n}×{n} square matrix,"
                " but got {r}×{c}."
            ).format(n=n_obs, r=n_rows, c=n_cols),
        )
    return sigma_df


def validate_panel_iv_columns(
    analysis: PanelIvParams,
    column_name_list: list[str],
    df_schema: pl.Schema,
) -> None:
    """PanelIV の entity_id / time / endog / instruments 列チェック。

    識別条件 (len(instruments) >= len(endog)) もここで確認する。
    """
    validate_existence(
        value=analysis.entity_id_column,
        valid_list=column_name_list,
        target=_PARAM_NAMES["entity_id_column"],
    )
    validate_numeric_types(
        schema=df_schema,
        columns=analysis.entity_id_column,
        target=_PARAM_NAMES["entity_id_column"],
    )
    if analysis.time_column:
        validate_existence(
            value=analysis.time_column,
            valid_list=column_name_list,
            target=_PARAM_NAMES["time_column"],
        )
    if analysis.endogenous_variables:
        validate_existence(
            value=analysis.endogenous_variables,
            valid_list=column_name_list,
            target=_PARAM_NAMES["endogenous_variables"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=analysis.endogenous_variables,
            target=_PARAM_NAMES["endogenous_variables"],
        )
    if analysis.instrumental_variables:
        validate_existence(
            value=analysis.instrumental_variables,
            valid_list=column_name_list,
            target=_PARAM_NAMES["instrumental_variables"],
        )
        validate_numeric_types(
            schema=df_schema,
            columns=analysis.instrumental_variables,
            target=_PARAM_NAMES["instrumental_variables"],
        )

"""
回帰分析共通バリデーション関数

各回帰モデルクラスから呼び出される純粋バリデーション関数群。
"""

import polars as pl

from economicon.schemas.entities import (
    FEParams,
    InstrumentalVariablesParams,
    REParams,
)
from economicon.services.data.tables_store import TablesStore
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

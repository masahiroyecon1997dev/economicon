import json
from pathlib import Path

import polars as pl
import pytest
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from main import app

_TEST_DATA_DIR = (
    Path(__file__).resolve().parents[3] / "test" / "data" / "parquet"
)
_BENCH_PY_DIR = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "benchmarks"
    / "python"
    / "synthetic"
)


def load_statistics_gold(model: str) -> dict:
    path = _BENCH_PY_DIR / f"synthetic_{model}_gold.json"
    with path.open(encoding="utf-8") as file_obj:
        return json.load(file_obj)


def load_statistics_gold_case(model: str, case_id: str) -> dict:
    cases = load_statistics_gold(model)["estimates"]["cases"]
    for case in cases:
        if case["case_id"] == case_id:
            return case
    raise KeyError(f"gold case not found: {model}/{case_id}")


def _read_dataset(name: str) -> pl.DataFrame:
    return pl.read_parquet(_TEST_DATA_DIR / f"{name}.parquet")


def _stat_group_frame(groups: pl.DataFrame, table_name: str) -> pl.DataFrame:
    return groups.filter(pl.col("table_name") == table_name).select("value")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def tables_store():
    manager = TablesStore()
    manager.clear_tables()
    AnalysisResultStore().clear_all()

    core = _read_dataset("synthetic_statistics_core")
    nulls = _read_dataset("synthetic_statistics_nulls")
    constant = _read_dataset("synthetic_statistics_constant")
    ci = _read_dataset("synthetic_statistics_ci")
    ci_invalid = _read_dataset("synthetic_statistics_ci_invalid")
    groups = _read_dataset("synthetic_statistics_test_groups")

    numeric_table = core.select(["A", "B", "C"])
    string_table = core.select(
        [
            "name",
            "category",
            pl.col("A").alias("score"),
        ]
    )

    manager.store_table("TestTableNumeric", numeric_table)
    manager.store_table("DSResultTableNumeric", core.select(["A", "B"]))
    manager.store_table("TestTableString", string_table)
    manager.store_table("DSResultTableString", string_table.select(["name"]))
    manager.store_table("TestNulls", nulls.select(["X"]))

    manager.store_table("ConfidenceTestTable", ci)
    manager.store_table("CIResultTestTable", ci)
    manager.store_table(
        "TextTable", ci_invalid.select(["numeric_col", "text_col"])
    )
    manager.store_table("EmptyTable", ci_invalid.select(["empty_col"]))

    manager.store_table(
        "StatTestTableA", _stat_group_frame(groups, "StatTestTableA")
    )
    manager.store_table(
        "StatTestTableB", _stat_group_frame(groups, "StatTestTableB")
    )
    manager.store_table(
        "StatTestTableC", _stat_group_frame(groups, "StatTestTableC")
    )
    manager.store_table(
        "StatTestTableSmall",
        _stat_group_frame(groups, "StatTestTableSmall"),
    )
    manager.store_table(
        "STResultTableA", _stat_group_frame(groups, "StatTestTableA")
    )
    manager.store_table(
        "STResultTableB", _stat_group_frame(groups, "StatTestTableB")
    )
    manager.store_table(
        "STResultTableC", _stat_group_frame(groups, "StatTestTableC")
    )

    manager.store_table("TestTable", core.select(["A", "B", "C", "D"]))
    manager.store_table("TestTableWithNulls", nulls.select(["X", "Y"]))
    manager.store_table("TestTableSparse", nulls.select(["P", "Q"]))
    manager.store_table("TestTableConstant", constant)
    manager.store_table("日本語テーブル", core.select(["変数A", "変数B"]))
    manager.store_table(
        "TestTableLarge", core.select(["V1", "V2", "V3", "V4", "V5"])
    )

    yield manager

    manager.clear_tables()
    AnalysisResultStore().clear_all()


@pytest.fixture
def tables_store_with_nulls(tables_store):
    return tables_store

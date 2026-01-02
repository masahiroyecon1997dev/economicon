import uuid

import polars as pl


class TableInfo:
    """
    テーブル情報を保持するデータクラス
    """
    _table_id = str
    _table_name: str
    _table: pl.DataFrame
    _num_columns: int = 0
    _num_rows: int = 0
    _description: str = ""

    def __init__(self, table_name: str, table: pl.DataFrame):
        self._id = str(uuid.uuid4())
        self._table_name = table_name
        self._table = table
        self._num_columns = table.width
        self._num_rows = table.height

    @property
    def table_id(self) -> str:
        return self._id

    @property
    def table_name(self) -> str:
        return self._table_name

    @property
    def table(self) -> pl.DataFrame:
        return self._table

    @property
    def num_columns(self) -> int:
        return self._num_columns

    @property
    def num_rows(self) -> int:
        return self._num_rows

    @property
    def description(self) -> str:
        return self._description

    @table_name.setter
    def table_name(self, table_name: str):
        self._table_name = table_name

    @table.setter
    def table(self, table: pl.DataFrame):
        self._table = table
        self._num_columns = table.width
        self._num_rows = table.height

    @description.setter
    def description(self, description: str):
        self._description = description


all_tables_info = {}

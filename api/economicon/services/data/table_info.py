import uuid

import polars as pl


class TableInfo:
    """
    テーブル情報を保持するデータクラス
    """

    _table_id = str
    _table_name: str
    _table: pl.DataFrame
    _description: str = ""

    def __init__(self, table_name: str, table: pl.DataFrame):
        self._id = str(uuid.uuid4())
        self._table_name = table_name
        self._table = table

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
    def column_count(self) -> int:
        return len(self._table.columns)

    @property
    def row_count(self) -> int:
        # return self._table.select(pl.len()).collect().item()
        return self._table.height

    @property
    def description(self) -> str:
        return self._description

    @table_name.setter
    def table_name(self, table_name: str):
        self._table_name = table_name

    @table.setter
    def table(self, table: pl.DataFrame):
        self._table = table

    @description.setter
    def description(self, description: str):
        self._description = description

from dataclasses import dataclass
import polars as pl
from typing import Dict


@dataclass
class TableInfo:
    """
    テーブル情報を保持するデータクラス
    """
    __table_name: str
    __table: pl.DataFrame
    __num_columns: int = 0
    __num_rows: int = 0
    __description: str = ""

    def __init__(self, table_name: str, table: pl.DataFrame):
        self.__table_name = table_name
        self.__table = table
        self.__num_columns = table.width
        self.__num_rows = table.height

    @property
    def table_name(self) -> str:
        return self.__table_name

    @property
    def table(self) -> pl.DataFrame:
        return self.__table

    @property
    def num_columns(self) -> int:
        return self.__num_columns

    @property
    def num_rows(self) -> int:
        return self.__num_rows

    @property
    def description(self) -> str:
        return self.__description

    @table_name.setter
    def table_name(self, table_name: str):
        self.__table_name = table_name

    @table.setter
    def table(self, table: pl.DataFrame):
        self.__table = table
        self.__num_columns = table.width
        self.__num_rows = table.height

    @description.setter
    def description(self, description: str):
        self.__description = description


all_tables_info: Dict[str, TableInfo] = {}

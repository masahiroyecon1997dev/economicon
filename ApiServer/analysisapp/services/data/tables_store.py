import threading
from typing import Dict, List

import polars as pl

from .table_info import TableInfo


class TablesStore:

    _instance = None
    _lock: threading.RLock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 初期化が一度だけ行われるようにする
        if not hasattr(self, '_initialized'):
            self._tables: Dict[str, TableInfo] = {}
            self._lock = threading.RLock()
            self._initialized = True

    def store_table(self, table_name: str, df: pl.DataFrame) -> str:
        with self._lock:
            table_info = TableInfo(table_name=table_name, table=df.clone())
            self._tables[table_name] = table_info
            return table_name

    def get_table(self, table_name: str) -> TableInfo:
        with self._lock:
            table_info = self._tables.get(table_name)
            if table_info:
                return table_info
            else:
                raise KeyError(f"Table '{table_name}' does not exist.")

    def get_column_name_list(self, table_name: str) -> List[str]:
        with self._lock:
            table_info = self._tables.get(table_name)
            if table_info:
                return table_info.table.columns
            else:
                raise KeyError(f"Table '{table_name}' does not exist.")

    def get_column_info_list(self, table_name: str) -> pl.Schema:
        with self._lock:
            table_info = self._tables.get(table_name)
            if table_info:
                return table_info.table.schema
            else:
                raise KeyError(f"Table '{table_name}' does not exist.")

    def rename_table(self, old_table_name: str, new_table_name: str) -> str:
        with self._lock:
            table_info = self._tables.pop(old_table_name)
            if table_info:
                table_info.table_name = new_table_name
                self._tables[new_table_name] = table_info
                return table_info.table_name
            else:
                raise KeyError(f"Table '{old_table_name}' does not exist.")

    def update_table(self, table_name: str, df: pl.DataFrame) -> str:
        with self._lock:
            table_info = self._tables.get(table_name)
            if table_info:
                table_info.table = df
                return table_name
            else:
                raise KeyError(f"Table '{table_name}' does not exist.")

    def delete_table(self, table_name: str) -> str:
        with self._lock:
            del self._tables[table_name]
            return table_name

    def get_table_name_list(self) -> List[str]:
        with self._lock:
            return list(self._tables.keys())

    def clear_tables(self):
        with self._lock:
            self._tables.clear()
            return True

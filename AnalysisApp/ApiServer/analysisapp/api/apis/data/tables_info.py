from dataclasses import dataclass
import polars as pl
from typing import Dict


@dataclass
class TableInfo:
    """
    テーブル情報を保持するデータクラス
    """
    table_name: str
    table: pl.DataFrame
    num_columns: int = 0
    num_rows: int = 0

    def __post_init__(self):
        self.num_columns = self.table.width
        self.num_rows = self.table.height


all_tables_info: Dict[str, TableInfo] = {}

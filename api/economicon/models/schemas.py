from .common import BaseRequest
from .types import ColumnName


class SortInstruction(BaseRequest):
    column_name: ColumnName
    ascending: bool

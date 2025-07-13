import io
import polars as pl
from typing import Dict
from django.utils.translation import gettext as _
from ..data.tables_info import TableInfo, all_tables_info
from ..utilities.create_table_name import create_table_name_by_file_name
from .common_api_class import AbstractApi, ApiError


class ImportExcelByFile(AbstractApi):
    """
    EXCELファイルインポートAPIのPythonロジック
    """
    def __init__(self, file_name: str, file_bytes: bytes):
        self.file_name = file_name
        self.file_bytes = file_bytes

    def validate(self):
        pass

    def execute(self):
        try:
            table_name = create_table_name_by_file_name(self.file_name,
                                                        all_tables_info)
            df = pl.read_excel(io.BytesIO(self.file_bytes))
            table_info = TableInfo(table_name=table_name, table=df)
            all_tables_info[table_name] = table_info
            result = {'tableName': table_name}
            return result
        except pl.NoDataError as e:
            message = _("The uploaded EXCEL file is empty or "
                        "contains no valid data.")
            raise ApiError(message) from e
        except pl.ComputeError as e:
            message = _("Failed to parse EXCEL file: "
                        "Invalid format or encoding.")
            raise ApiError(message) from e
        except Exception as e:
            message = _('An unexpected error occurred during EXCEL processing')
            raise ApiError(message) from e


def import_excel_by_file(file_name: str, file_bytes: bytes) -> Dict:
    api = ImportExcelByFile(file_name, file_bytes)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result

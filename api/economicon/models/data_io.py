"""インポート関連のスキーマ定義"""

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from .common import BaseRequest
from .types import FilePath, NewTableName, Separator, TableName


class ImportCsvByPathRequestBody(BaseRequest):
    """CSVファイルパス指定インポートリクエスト"""

    file_path: Annotated[
        FilePath, Field(description="インポートするCSVファイルのパス")
    ]
    table_name: NewTableName
    separator: Annotated[Separator, Field(description="区切り文字")] = ","


class ImportExcelByPathRequestBody(BaseRequest):
    """Excelファイルパス指定インポートリクエスト"""

    file_path: Annotated[
        FilePath, Field(description="インポートするExcelファイルのパス")
    ]
    table_name: NewTableName
    sheet_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=31,  # Excelの絶対ルール
            # 禁止記号 \ / ? * : [ ] を除外し、先頭末尾の ' も防ぐ正規表現
            pattern=r"^(?!')[^\\/?*:\[\]]+(?<!')$",
        ),
        Field(
            examples=["人口動態", "Sheet1"],
            description="Excelのシート名（31文字以内、使用不可記号あり）",
        ),
    ]


class ImportParquetByPathRequestBody(BaseRequest):
    """Parquetファイルパス指定インポートリクエスト"""

    file_path: Annotated[
        FilePath, Field(description="インポートするParquetファイルのパス")
    ]
    table_name: NewTableName


class ExportCsvByPathRequestBody(BaseRequest):
    """CSVファイルパス指定エクスポートリクエスト"""

    table_name: TableName
    file_path: Annotated[
        FilePath, Field(description="出力するCSVファイルのパス")
    ]
    separator: Separator


class ExportExcelByPathRequestBody(BaseModel):
    """Excelファイルパス指定エクスポートリクエスト"""

    table_name: TableName
    file_path: Annotated[
        FilePath, Field(description="出力するExcelファイルのパス")
    ]


class ExportParquetByPathRequestBody(BaseModel):
    """Parquetファイルパス指定エクスポートリクエスト"""

    table_name: TableName
    file_path: Annotated[
        FilePath, Field(description="出力するParquetファイルのパス")
    ]

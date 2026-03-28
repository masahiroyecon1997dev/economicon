from typing import Annotated, Literal

from pydantic import AfterValidator, Field, StringConstraints

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import (
    BernoulliParams,
    BetaParams,
    BinomialParams,
    ExponentialParams,
    FixedParams,
    GammaParams,
    GeometricParams,
    HypergeometricParams,
    LognormalParams,
    LogParams,
    NegativeBinomialParams,
    NormalParams,
    PoissonParams,
    PowerParams,
    RootParams,
    UniformParams,
    WeibullParams,
)

NAME_PATTERN = r"^[^\x00-\x1f\x7f]+$"


def validate_sheet_name_quotes(v: str) -> str:
    """先頭と末尾の引用符をチェックする関数"""
    if v.startswith("'") or v.endswith("'"):
        # _() は翻訳関数として定義されている前提
        raise ValueError(
            _("Sheet name cannot start or end with a single quote")
        )
    return v


def validate_file_name_chars(v: str) -> str:
    """
    ファイル名としての整合性をチェックする関数。
    """
    # 1. 先頭のドット禁止
    if v.startswith("."):
        raise ValueError(_("File name cannot start with a dot (.)"))

    # 2. 末尾のスペースまたはドット禁止 (Windows制限対策)
    if v.endswith(" ") or v.endswith("."):
        raise ValueError(_("File name cannot end with a space or a dot"))

    # 3. 予約名のチェック (CON, PRN, AUX, NUL など)
    # 大文字小文字問わず、拡張子があってもなくてもダメ
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    base_name = v.split(".", maxsplit=1)[0].upper()
    if base_name in reserved_names:
        raise ValueError(_(f"'{base_name}' is a reserved system name"))

    return v


TableName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    Field(
        title="Table Name",
        examples=["population_data", "市区町村人口データ"],
        description="テーブル名",
    ),
]

NewTableName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=NAME_PATTERN,
    ),
    Field(
        title="New Table Name",
        examples=["population_data", "市区町村人口データ"],
        description="新しいテーブル名",
    ),
]

ColumnName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    Field(
        title="Column Name",
        examples=["population", "人口"],
        description="カラム名",
    ),
]

NewColumnName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=NAME_PATTERN,
    ),
    Field(
        title="New Column Name",
        examples=["population", "人口"],
        description="新しいカラム名",
    ),
]

FilePath = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1024),
    Field(
        title="File Path",
        examples=["/path/to/file.csv", "C:\\data\\file.csv"],
        description="ファイルのパス",
    ),
]

DirectoryPath = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=1024,
    ),
    Field(
        title="Directory Path",
        examples=["/path/to/directory", "C:\\data\\directory"],
        description="ディレクトリのパス",
    ),
]

Separator = Annotated[
    str,
    StringConstraints(min_length=1, max_length=10),
    Field(
        title="Separator",
        examples=[",", "\t"],
        description="区切り文字",
    ),
]

ExcelSheetName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=31,
        # 禁止記号 \ / ? * : [ ] を除外
        pattern=r"^[^/\\?*:\[\]]+$",
    ),
    # field_validatorの代わりにAfterValidatorでロジックを注入
    AfterValidator(validate_sheet_name_quotes),
    Field(
        title="Excel Sheet Name",
        examples=["人口動態", "Sheet1"],
        description="Excelのシート名（31文字以内、使用不可記号あり）",
    ),
]

FileName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=255,
        # 禁止記号
        pattern=r'^[^\\/:*?"<>|]+$',
    ),
    AfterValidator(validate_file_name_chars),
    Field(
        title="File Name",
        examples=["report_2024", "analysis_result"],
        description="OSで使用可能なファイル名（記号制限あり）",
    ),
]

# Polars の read_csv でサポートされるエンコーディング
# shift_jis は実装上 MS932 (CP932) として扱われる
CsvEncoding = Literal[
    "utf8",
    "latin1",
    "ascii",
    "gbk",
    "windows-1252",
    "shift_jis",
]

# エクスポートするファイル形式
ExportFormat = Literal["csv", "excel", "parquet"]

type DistributionParams = (
    UniformParams
    | ExponentialParams
    | NormalParams
    | GammaParams
    | BetaParams
    | WeibullParams
    | LognormalParams
    | BinomialParams
    | BernoulliParams
    | PoissonParams
    | GeometricParams
    | HypergeometricParams
    | NegativeBinomialParams
    | FixedParams
)

type DistributionConfig = Annotated[
    DistributionParams,
    Field(discriminator="type", description="分布設定"),
]

type TransformMethodParams = LogParams | PowerParams | RootParams

type TransformMethodConfig = Annotated[
    TransformMethodParams,
    Field(discriminator="method", description="変換方法設定"),
]

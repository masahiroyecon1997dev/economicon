from typing import Annotated, Union

from pydantic import Field, StringConstraints

from .common import (
    BernoulliParams,
    BetaParams,
    BinomialParams,
    ExponentialParams,
    GammaParams,
    GeometricParams,
    HypergeometricParams,
    LognormalParams,
    LogParams,
    NormalParams,
    PoissonParams,
    PowerParams,
    RootParams,
    UniformParams,
    WeibullParams,
)

NAME_PATTERN = r"^[^\x00-\x1f\x7f]+$"

TableName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    Field(
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
        examples=["population_data", "市区町村人口データ"],
        description="新しいテーブル名",
    ),
]

ColumnName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    Field(
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
        examples=["population", "人口"],
        description="新しいカラム名",
    ),
]

FilePath = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1024),
    Field(
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
        examples=["/path/to/directory", "C:\\data\\directory"],
        description="ディレクトリのパス",
    ),
]

FileName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=255,
        pattern=r'^(?!\.)[^\\/:*?"<>|]+(?<![ .])$',
    ),
    Field(
        examples=["output.csv", "人口動態データ.xlsx"],
        description="ファイル名",
    ),
]

Separator = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10),
    Field(
        examples=[",", "\t"],
        description="区切り文字",
    ),
]

type DistributionParams = Union[
    UniformParams,
    ExponentialParams,
    NormalParams,
    GammaParams,
    BetaParams,
    WeibullParams,
    LognormalParams,
    BinomialParams,
    BernoulliParams,
    PoissonParams,
    GeometricParams,
    HypergeometricParams,
]

type DistributionConfig = Annotated[
    DistributionParams,
    Field(discriminator="type", description="分布設定"),
]

type TransformMethodParams = Union[
    LogParams,
    PowerParams,
    RootParams,
]

type TransformMethodConfig = Annotated[
    TransformMethodParams,
    Field(discriminator="method", description="変換方法設定"),
]

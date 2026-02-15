from enum import Enum
from typing import Annotated

from pydantic import Field, StringConstraints

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


class DistributionType(str, Enum):
    UNIFORM = "uniform"
    EXPONENTIAL = "exponential"
    NORMAL = "normal"
    GAMMA = "gamma"
    BETA = "beta"
    WEIBULL = "weibull"
    LOGNORMAL = "lognormal"
    BINOMIAL = "binomial"
    BERNOULLI = "bernoulli"
    POISSON = "poisson"
    GEOMETRIC = "geometric"
    HYPERGEOMETRIC = "hypergeometric"

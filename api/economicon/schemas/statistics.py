"""統計解析関連のスキーマ定義"""

from typing import Annotated, Any

from pydantic import BeforeValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from economicon.schemas.common import BaseRequest, BaseResult
from economicon.schemas.enums import (
    AlternativeHypothesis,
    ConfidenceIntervalStatisticsType,
    CorrelationMethod,
    DescriptiveStatisticType,
    MissingHandlingMethod,
    StatisticalTestType,
)
from economicon.schemas.types import ColumnName, TableName

# ---------------------------------------------------------------------------
# 信頼区間計算
# ---------------------------------------------------------------------------


def _coerce_statistic_type(
    v: Any,
) -> ConfidenceIntervalStatisticsType:
    """JSON文字列をConfidenceIntervalStatisticsTypeに変換するBeforeValidator"""
    if isinstance(v, ConfidenceIntervalStatisticsType):
        return v
    if isinstance(v, str):
        try:
            return ConfidenceIntervalStatisticsType(v)
        except ValueError:
            valid = ", ".join(
                e.value for e in ConfidenceIntervalStatisticsType
            )
            raise PydanticCustomError(
                "literal_error",
                "statisticType must be one of: {expected}",
                {"expected": valid},
            ) from None
    return v


class ConfidenceIntervalRequestBody(BaseRequest):
    """信頼区間計算リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="信頼区間を計算する対象テーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    column_name: Annotated[
        ColumnName,
        Field(
            title="Column Name",
            description="信頼区間を計算する対象カラム名。テーブル内に存在するカラム名を指定してください。",
        ),
    ]
    confidence_level: Annotated[
        float,
        Field(
            title="Confidence Level",
            description="信頼水準（例: 0.95 = 95%信頼区間）",
            gt=0.0,
            lt=1.0,
        ),
    ]
    statistic_type: Annotated[
        ConfidenceIntervalStatisticsType,
        BeforeValidator(_coerce_statistic_type),
        Field(
            title="Statistic Type",
            description="信頼区間を計算する統計量のタイプ。"
            "（mean: 平均、median: 中央値、proportion: 割合、"
            "variance: 分散、standard_deviation: 標準偏差）",
        ),
    ]


class ConfidenceIntervalResult(BaseResult):
    """
    信頼区間計算レスポンス。
    詳細は GET /api/analysis/results/{resultId} で取得できる
    """

    result_id: str = Field(
        title="Result ID",
        description=(
            "分析結果の一意 ID。"
            "詳細は GET /api/analysis/results/{resultId} で取得可能。"
        ),
    )


# ---------------------------------------------------------------------------
# 記述統計
# ---------------------------------------------------------------------------


class DescriptiveStatisticsRequestBody(BaseRequest):
    """記述統計リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="記述統計を計算する対象テーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    column_name_list: Annotated[
        list[ColumnName],
        Field(
            title="Column Name List",
            description="記述統計を計算する対象カラム名のリスト。テーブル内に存在するカラム名を指定してください。複数カラムを指定することもできます。",
            min_length=1,
        ),
    ]
    statistics: Annotated[
        list[DescriptiveStatisticType],
        Field(
            title="Statistics",
            description="計算する統計量のリスト"
            "（mean: 平均、median: 中央値、mode: 最頻値、"
            "variance: 不偏分散、std_dev: 標準偏差、"
            "range: 範囲、iqr: 四分位数範囲、"
            "count: 有効サンプル数、null_count: null数、"
            "null_ratio: null割合、"
            "population_variance: 母分散）",
            min_length=1,
        ),
    ]

    @field_validator("statistics", mode="before")
    @classmethod
    def coerce_statistics(cls, v: Any) -> Any:
        """JSON文字列をDescriptiveStatisticTypeに変換するfield_validator"""
        if not isinstance(v, list):
            return v
        result = []
        for item in v:
            if isinstance(item, DescriptiveStatisticType):
                result.append(item)
            elif isinstance(item, str):
                try:
                    result.append(DescriptiveStatisticType(item))
                except ValueError:
                    valid = ", ".join(
                        e.value for e in DescriptiveStatisticType
                    )
                    raise PydanticCustomError(
                        "literal_error",
                        "statistics must be one of: {expected}",
                        {"expected": valid},
                    ) from None
            else:
                result.append(item)
        return result


class DescriptiveStatisticsResult(BaseResult):
    """
    記述統計レスポンス。
    詳細は GET /api/analysis/results/{resultId} で取得できる
    """

    result_id: str = Field(
        title="Result ID",
        description=(
            "分析結果の一意 ID。"
            "詳細は GET /api/analysis/results/{resultId} で取得可能。"
        ),
    )


# ---------------------------------------------------------------------------
# 相関係数テーブル作成
# ---------------------------------------------------------------------------


def _coerce_correlation_method(v: Any) -> CorrelationMethod:
    """JSON文字列をCorrelationMethodに変換するBeforeValidator"""
    if isinstance(v, CorrelationMethod):
        return v
    if isinstance(v, str):
        try:
            return CorrelationMethod(v)
        except ValueError:
            valid = ", ".join(e.value for e in CorrelationMethod)
            raise PydanticCustomError(
                "literal_error",
                "method must be one of: {expected}",
                {"expected": valid},
            ) from None
    return v


def _coerce_missing_handling(v: Any) -> MissingHandlingMethod:
    """JSON文字列をMissingHandlingMethodに変換するBeforeValidator"""
    if isinstance(v, MissingHandlingMethod):
        return v
    if isinstance(v, str):
        try:
            return MissingHandlingMethod(v)
        except ValueError:
            valid = ", ".join(e.value for e in MissingHandlingMethod)
            raise PydanticCustomError(
                "literal_error",
                "missingHandling must be one of: {expected}",
                {"expected": valid},
            ) from None
    return v


class CreateCorrelationTableRequestBody(BaseRequest):
    """相関係数テーブル作成リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="相関係数を計算する元テーブル名。",
        ),
    ]
    column_names: Annotated[
        list[ColumnName],
        Field(
            title="Column Names",
            description=(
                "相関係数を計算する対象カラム名のリスト。2列以上を指定してください。"
            ),
            min_length=2,
        ),
    ]
    new_table_name: Annotated[
        TableName,
        Field(
            title="New Table Name",
            description="結果を格納する新規テーブル名。",
        ),
    ]
    method: Annotated[
        CorrelationMethod,
        BeforeValidator(_coerce_correlation_method),
        Field(
            title="Correlation Method",
            description=(
                "相関係数の計算手法。"
                "pearson: ピアソン積率相関係数（デフォルト）、"
                "spearman: スピアマン順位相関係数、"
                "kendall: ケンドールの順位相関係数"
            ),
            default=CorrelationMethod.PEARSON,
        ),
    ] = CorrelationMethod.PEARSON
    decimal_places: Annotated[
        int,
        Field(
            title="Decimal Places",
            description="丸め桁数（1～15、デフォルト: 3）",
            ge=1,
            le=15,
            default=3,
        ),
    ] = 3
    lower_triangle_only: Annotated[
        bool,
        Field(
            title="Lower Triangle Only",
            description=(
                "True の場合、上三角部分の値を null に置き換えて返す。"
                "デフォルト: False。"
            ),
            default=False,
        ),
    ] = False
    missing_handling: Annotated[
        MissingHandlingMethod,
        BeforeValidator(_coerce_missing_handling),
        Field(
            title="Missing Handling",
            description=(
                "欠損値の処理方法。"
                "pairwise: ペア単位で欠損を除外して計算（デフォルト）、"
                "listwise: 欠損を含む行をすべての列で一括削除してから計算"
            ),
            default=MissingHandlingMethod.PAIRWISE,
        ),
    ] = MissingHandlingMethod.PAIRWISE


class CreateCorrelationTableResult(BaseResult):
    """相関係数テーブル作成レスポンス"""

    table_name: str = Field(
        title="Table Name",
        description="新規作成された相関係数テーブルの名前。",
    )


# ---------------------------------------------------------------------------
# 統計検定
# ---------------------------------------------------------------------------


def _coerce_test_type(v: Any) -> StatisticalTestType:
    """JSON文字列を StatisticalTestType に変換する"""
    if isinstance(v, StatisticalTestType):
        return v
    if isinstance(v, str):
        try:
            return StatisticalTestType(v)
        except ValueError:
            valid = ", ".join(e.value for e in StatisticalTestType)
            raise PydanticCustomError(
                "literal_error",
                "testType must be one of: {expected}",
                {"expected": valid},
            ) from None
    return v


def _coerce_alternative(v: Any) -> AlternativeHypothesis:
    """JSON文字列を AlternativeHypothesis に変換する"""
    if isinstance(v, AlternativeHypothesis):
        return v
    if isinstance(v, str):
        try:
            return AlternativeHypothesis(v)
        except ValueError:
            valid = ", ".join(e.value for e in AlternativeHypothesis)
            raise PydanticCustomError(
                "literal_error",
                "alternative must be one of: {expected}",
                {"expected": valid},
            ) from None
    return v


# サンプル数バリデーション用定数
_MIN_F_TEST_SAMPLES: int = 2
_MAX_TZ_TEST_SAMPLES: int = 2


class SampleInput(BaseRequest):
    """検定に使用する1サンプルの指定（テーブル名・列名のペア）"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="サンプルを取得するテーブル名。",
        ),
    ]
    column_name: Annotated[
        ColumnName,
        Field(
            title="Column Name",
            description="サンプルとして使用する列名。",
        ),
    ]


class StatisticalTestOptions(BaseRequest):
    """統計検定のオプション設定"""

    alternative: Annotated[
        AlternativeHypothesis,
        BeforeValidator(_coerce_alternative),
        Field(
            title="Alternative Hypothesis",
            description=(
                "対立仮説の方向。"
                "two-sided: 両側検定（デフォルト）、"
                "larger: 右側検定、smaller: 左側検定"
            ),
            default=AlternativeHypothesis.TWO_SIDED,
        ),
    ] = AlternativeHypothesis.TWO_SIDED
    mu: Annotated[
        float | None,
        BeforeValidator(lambda v: float(v) if v is not None else None),
        Field(
            title="Mu",
            description=("1 群検定における比較基準値（デフォルト: 0.0）"),
            default=None,
        ),
    ] = None
    paired: Annotated[
        bool,
        Field(
            title="Paired",
            description=("対応のある検定を行うかどうか（デフォルト: False）"),
            default=False,
        ),
    ] = False
    equal_var: Annotated[
        bool,
        Field(
            title="Equal Variance",
            description=(
                "t 検定で等分散を仮定するかどうか。"
                "False の場合は Welch の t 検定を使用"
                "（デフォルト: True）"
            ),
            default=True,
        ),
    ] = True


class StatisticalTestRequestBody(BaseRequest):
    """統計検定リクエスト"""

    test_type: Annotated[
        StatisticalTestType,
        BeforeValidator(_coerce_test_type),
        Field(
            title="Test Type",
            description=(
                "実行する統計検定の種類。"
                "t-test: t 検定、z-test: z 検定、"
                "f-test: F 検定 / ANOVA"
            ),
        ),
    ]
    samples: Annotated[
        list[SampleInput],
        Field(
            title="Samples",
            description=(
                "比較対象となるサンプルのリスト。"
                "各要素にテーブル名と列名を指定する。"
            ),
            min_length=1,
        ),
    ]
    options: Annotated[
        StatisticalTestOptions,
        Field(
            title="Options",
            description=(
                "検定オプション（対立仮説・等分散仮定・対応の有無など）"
            ),
            default_factory=StatisticalTestOptions,
        ),
    ]

    @model_validator(mode="before")
    @classmethod
    def set_default_options(cls, values: Any) -> Any:
        """options が未指定の場合にデフォルトを設定する"""
        if isinstance(values, dict) and "options" not in values:
            values["options"] = {}
        return values

    @model_validator(mode="after")
    def validate_sample_count(
        self,
    ) -> StatisticalTestRequestBody:
        """
        検定種別に応じたサンプル数のバリデー
        ション。
        """
        n = len(self.samples)
        match self.test_type:
            case StatisticalTestType.F_TEST:
                if n < _MIN_F_TEST_SAMPLES:
                    raise ValueError(
                        f"f-test requires at least"
                        f" {_MIN_F_TEST_SAMPLES} samples,"
                        f" but got {n}"
                    )
            case StatisticalTestType.T_TEST | StatisticalTestType.Z_TEST:
                if n > _MAX_TZ_TEST_SAMPLES:
                    raise ValueError(
                        f"{self.test_type.value} supports up to"
                        f" {_MAX_TZ_TEST_SAMPLES} samples,"
                        f" but got {n}"
                    )
        return self


class StatisticalTestResult(BaseResult):
    """
    統計検定レスポンス。
    詳細は GET /api/analysis/results/{resultId} で取得できる
    """

    result_id: str = Field(
        title="Result ID",
        description=(
            "分析結果の一意 ID。"
            "詳細は GET /api/analysis/results/{resultId} で取得可能。"
        ),
    )

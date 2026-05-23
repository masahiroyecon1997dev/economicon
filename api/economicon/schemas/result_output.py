"""分析結果出力関連のスキーマ定義"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from economicon.schemas.common import BaseRequest, BaseResult


class StarConfig(BaseModel):
    """有意性記号の設定"""

    threshold: float = Field(description="有意水準の閾値（例: 0.05）")
    symbol: str = Field(
        description="有意性を示す記号（例: '**'）"
    )


type OutputResultFormat = Literal["latex", "markdown", "text"]


class RegressionOutputOptions(BaseRequest):
    """回帰結果出力オプション"""

    stat_in_parentheses: Annotated[
        Literal["se", "t", "p", "none"],
        Field(
            default="se",
            description=(
                "括弧内に表示する統計量。"
                "se: 標準誤差、t: t 値、p: p 値、"
                "none: 括弧行なし"
            ),
        ),
    ] = "se"
    significance_stars: Annotated[
        list[StarConfig] | None,
        Field(
            default=None,
            description=(
                "有意性記号の設定リスト。"
                "None の場合はデフォルト設定を使用 "
                "(0.01:***, 0.05:**, 0.1:*)"
            ),
        ),
    ] = None
    variable_labels: Annotated[
        dict[str, str] | None,
        Field(
            default=None,
            description=(
                "変数名から表示ラベルへのマッピング辞書。"
                "未設定の変数は変数名をそのまま使用。"
            ),
        ),
    ] = None
    const_at_bottom: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "True の場合、定数項を変数リストの最下部に配置する。"
            ),
        ),
    ] = True
    variable_order: Annotated[
        list[str] | None,
        Field(
            default=None,
            description=(
                "変数の表示順序を明示的に指定するリスト。"
                "指定した変数は先頭から順に表示される。"
                "リストに含まれない変数はその後ろに追加される。"
                "None の場合は推定結果への登場順を使用。"
            ),
        ),
    ] = None


class DescriptiveStatisticsOutputOptions(BaseRequest):
    """記述統計出力オプション"""

    include_result_name: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、結果名の列を出力に含める。",
        ),
    ] = True
    include_table_name: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、テーブル名の列を出力に含める。",
        ),
    ] = True
    variable_labels: Annotated[
        dict[str, str] | None,
        Field(
            default=None,
            description="変数名から表示ラベルへのマッピング辞書。",
        ),
    ] = None
    variable_order: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="変数の表示順序を指定するリスト。",
        ),
    ] = None
    statistic_labels: Annotated[
        dict[str, str] | None,
        Field(
            default=None,
            description="統計量名から表示ラベルへのマッピング辞書。",
        ),
    ] = None
    statistic_order: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="統計量列の表示順序を指定するリスト。",
        ),
    ] = None


class ConfidenceIntervalOutputOptions(BaseRequest):
    """信頼区間出力オプション"""

    include_result_name: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、結果名の列を出力に含める。",
        ),
    ] = True
    include_table_name: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、テーブル名の列を出力に含める。",
        ),
    ] = True
    include_confidence_level: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、信頼水準の列を出力に含める。",
        ),
    ] = True


class StatisticalTestOutputOptions(BaseRequest):
    """統計的検定出力オプション"""

    include_result_name: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、結果名の列を出力に含める。",
        ),
    ] = True
    include_table_name: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、テーブル名の列を出力に含める。",
        ),
    ] = True
    include_confidence_interval: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、信頼区間列を出力に含める。",
        ),
    ] = True
    include_confidence_level: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、信頼水準の列を出力に含める。",
        ),
    ] = True
    include_effect_size: Annotated[
        bool,
        Field(
            default=True,
            description="True の場合、効果量の列を出力に含める。",
        ),
    ] = True


class RegressionOutputRequest(BaseRequest):
    """回帰結果のフォーマット出力リクエスト"""

    result_type: Annotated[
        Literal["regression"],
        Field(description="出力対象の分析結果種別。"),
    ] = "regression"
    result_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="出力する分析結果 ID のリスト（1件以上）",
        ),
    ]
    format: Annotated[
        OutputResultFormat,
        Field(description="出力フォーマット。"),
    ]
    options: Annotated[
        RegressionOutputOptions,
        Field(
            default_factory=RegressionOutputOptions,
            description="回帰結果出力用オプション。",
        ),
    ] = Field(default_factory=RegressionOutputOptions)


class DescriptiveStatisticsOutputRequest(BaseRequest):
    """記述統計結果のフォーマット出力リクエスト"""

    result_type: Annotated[
        Literal["descriptive_statistics"],
        Field(description="出力対象の分析結果種別。"),
    ] = "descriptive_statistics"
    result_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="出力する分析結果 ID のリスト（1件以上）",
        ),
    ]
    format: Annotated[
        OutputResultFormat,
        Field(description="出力フォーマット。"),
    ]
    options: Annotated[
        DescriptiveStatisticsOutputOptions,
        Field(
            default_factory=DescriptiveStatisticsOutputOptions,
            description="記述統計出力用オプション。",
        ),
    ] = Field(default_factory=DescriptiveStatisticsOutputOptions)


class ConfidenceIntervalOutputRequest(BaseRequest):
    """信頼区間結果のフォーマット出力リクエスト"""

    result_type: Annotated[
        Literal["confidence_interval"],
        Field(description="出力対象の分析結果種別。"),
    ] = "confidence_interval"
    result_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="出力する分析結果 ID のリスト（1件以上）",
        ),
    ]
    format: Annotated[
        OutputResultFormat,
        Field(description="出力フォーマット。"),
    ]
    options: Annotated[
        ConfidenceIntervalOutputOptions,
        Field(
            default_factory=ConfidenceIntervalOutputOptions,
            description="信頼区間出力用オプション。",
        ),
    ] = Field(default_factory=ConfidenceIntervalOutputOptions)


class StatisticalTestOutputRequest(BaseRequest):
    """統計的検定結果のフォーマット出力リクエスト"""

    result_type: Annotated[
        Literal["statistical_test"],
        Field(description="出力対象の分析結果種別。"),
    ] = "statistical_test"
    result_ids: Annotated[
        list[str],
        Field(
            min_length=1,
            description="出力する分析結果 ID のリスト（1件以上）",
        ),
    ]
    format: Annotated[
        OutputResultFormat,
        Field(description="出力フォーマット。"),
    ]
    options: Annotated[
        StatisticalTestOutputOptions,
        Field(
            default_factory=StatisticalTestOutputOptions,
            description="統計的検定出力用オプション。",
        ),
    ] = Field(default_factory=StatisticalTestOutputOptions)


type OutputResultRequest = Annotated[
    RegressionOutputRequest
    | DescriptiveStatisticsOutputRequest
    | ConfidenceIntervalOutputRequest
    | StatisticalTestOutputRequest,
    Field(discriminator="result_type"),
]


class OutputResultResult(BaseResult):
    """推定結果フォーマット出力レスポンス"""

    content: str = Field(description="フォーマット済み出力テキスト")
    format: str = Field(
        description="出力フォーマット (latex / markdown / text)"
    )

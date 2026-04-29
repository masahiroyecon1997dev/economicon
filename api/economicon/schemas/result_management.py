"""分析結果管理関連のスキーマ定義"""

from typing import Any

from pydantic import Field

from economicon.schemas.common import BaseResult


class AnalysisResultSummary(BaseResult):
    """分析結果サマリー（一覧取得用の各要素）"""

    id: str = Field(title="ID", description="分析結果の一意 ID")
    name: str = Field(title="Name", description="分析結果名")
    description: str = Field(
        title="Description",
        description="分析結果の説明メモ",
    )
    created_at: str = Field(
        title="Created At",
        description="作成日時（ISO 8601 形式）",
    )
    table_name: str = Field(
        title="Table Name",
        description="分析対象テーブル名",
    )
    result_type: str = Field(
        title="Result Type",
        description=(
            "分析種別文字列"
            "（regression / confidence_interval /"
            " descriptive_statistics / statistical_test /"
            " did / rdd / heckman 等）"
        ),
    )
    result_type_label: str = Field(
        title="Result Type Label",
        description="分析種別の表示ラベル（日本語）",
    )
    model_type: str | None = Field(
        title="Model Type",
        description="モデルの種別文字列（ols / fe / re / iv 等）",
    )
    summary_text: str = Field(
        title="Summary Text",
        description="分析内容の簡潔な説明文（フロントエンド一覧表示用）",
    )


class GetAllAnalysisResultsResult(BaseResult):
    """全分析結果サマリー取得レスポンス"""

    results: list[AnalysisResultSummary] = Field(
        title="Results",
        description="分析結果のサマリーリスト",
    )


class AnalysisResultDetail(BaseResult):
    """分析結果詳細（1件取得用）"""

    id: str = Field(title="ID", description="分析結果の一意 ID")
    name: str = Field(title="Name", description="分析結果名")
    description: str = Field(
        title="Description",
        description="分析結果の説明メモ",
    )
    table_name: str = Field(
        title="Table Name",
        description="分析対象テーブル名",
    )
    result_type: str = Field(
        title="Result Type",
        description=(
            "分析種別文字列"
            "（regression / confidence_interval /"
            " descriptive_statistics / statistical_test 等）"
        ),
    )
    result_data: dict[str, Any] = Field(
        title="Result Data",
        description=(
            "分析結果の詳細データ。"
            "分析種別（result_type）により含まれるキーが異なる。"
        ),
    )
    created_at: str = Field(
        title="Created At",
        description="作成日時（ISO 8601 形式）",
    )
    model_path: str | None = Field(
        title="Model Path",
        description="保存済みモデルファイルのパス（None の場合は未保存）",
    )
    model_type: str | None = Field(
        title="Model Type",
        description="モデルの種別文字列（ols / fe / re / iv 等）",
    )
    entity_id_column: str | None = Field(
        title="Entity ID Column",
        description="パネルデータ分析における個体 ID 列名",
    )
    time_column: str | None = Field(
        title="Time Column",
        description="パネルデータ分析における時間列名",
    )


class DeleteAnalysisResultResult(BaseResult):
    """分析結果削除レスポンス"""

    deleted_result_id: str = Field(
        title="Deleted Result ID",
        description="削除した分析結果の ID",
    )


class ClearAllAnalysisResultsResult(BaseResult):
    """全分析結果クリアレスポンス"""

    message: str = Field(
        title="Message",
        description="処理結果メッセージ",
    )

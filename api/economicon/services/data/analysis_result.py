import os
import pickle
import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from economicon.i18n.translation import gettext as _

# 分析種別 → 表示ラベルの翻訳キー（msgid）
_RESULT_TYPE_LABELS: dict[str, str] = {
    "regression": "regression",
    "confidence_interval": "confidence_interval",
    "descriptive_statistics": "descriptive_statistics",
    "statistical_test": "statistical_test",
    "did": "did",
    "rdd": "rdd",
    "heckman": "heckman",
}


class AnalysisResult:
    """
    分析結果を保持するデータクラス

    推定済みモデルオブジェクトは AppData/Local/economicon/tmp/models/
    配下に pickle ファイルとして保存し、メモリ上には保持しない。
    """

    _id: str
    _name: str
    _description: str
    _table_name: str
    _result_type: str
    _result_data: dict[str, Any]
    _created_at: str
    _model_path: str | None
    _model_type: str | None
    _entity_id_column: str | None
    _time_column: str | None
    # Tobit 欠損値除去後の元テーブル行インデックス（__row_idx__ 結合用）
    _row_indices: np.ndarray | None

    def __init__(
        self,
        *,
        name: str,
        description: str,
        table_name: str,
        result_data: dict[str, Any],
        result_type: str = "regression",
        model_type: str | None = None,
        entity_id_column: str | None = None,
        time_column: str | None = None,
        row_indices: np.ndarray | None = None,
    ):
        self._id = str(uuid.uuid4())
        self._name = name
        self._description = description
        self._table_name = table_name
        self._result_type = result_type
        self._result_data = result_data
        self._created_at = datetime.now().isoformat()
        self._model_path = None
        self._model_type = model_type
        self._entity_id_column = entity_id_column
        self._time_column = time_column
        self._row_indices = row_indices

    @staticmethod
    def get_tmp_models_dir() -> Path:
        """
        OS 別に一時モデル保存ディレクトリを解決・作成して返す。

        - Windows : %LOCALAPPDATA%/economicon/tmp/models/
        - macOS/Linux : ~/.cache/economicon/tmp/models/
        """
        os_system = platform.system()
        if os_system == "Windows":
            local_appdata = os.getenv("LOCALAPPDATA") or str(
                Path.home() / "AppData" / "Local"
            )
            tmp_dir = Path(local_appdata) / "economicon" / "tmp" / "models"
        else:
            tmp_dir = Path.home() / ".cache" / "economicon" / "tmp" / "models"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def table_name(self) -> str:
        return self._table_name

    @property
    def result_type(self) -> str:
        return self._result_type

    @property
    def result_data(self) -> dict[str, Any]:
        return self._result_data

    @property
    def created_at(self) -> str:
        return self._created_at

    @property
    def model_path(self) -> str | None:
        return self._model_path

    @property
    def model_type(self) -> str | None:
        return self._model_type

    @property
    def entity_id_column(self) -> str | None:
        return self._entity_id_column

    @property
    def time_column(self) -> str | None:
        return self._time_column

    @property
    def row_indices(self) -> np.ndarray | None:
        """欲存値除去後の元テーブル行インデックス (Tobit 等で使用)"""
        return self._row_indices

    @name.setter
    def name(self, name: str):
        self._name = name

    @description.setter
    def description(self, description: str):
        self._description = description

    # ------------------------------------------------------------------
    # モデルファイル操作
    # ------------------------------------------------------------------

    def save_model(self, model_object: Any) -> str:
        """
        推定済みモデルを pickle ファイルに保存する。

        保存パスは {get_tmp_models_dir()}/{self._id}.pkl に固定される。
        保存後、self._model_path を更新する。

        Args:
            model_object: pickle シリアライズ可能な推定済みモデル

        Returns:
            保存先ファイルパス（文字列）
        """
        tmp_dir = self.get_tmp_models_dir()
        file_path = tmp_dir / f"{self._id}.pkl"
        with open(file_path, "wb") as f:
            pickle.dump(model_object, f, protocol=pickle.HIGHEST_PROTOCOL)
        self._model_path = str(file_path)
        return self._model_path

    def load_model(self) -> Any:
        """
        保存済み pickle ファイルからモデルを読み込んで返す。

        Returns:
            pickle でデシリアライズされたモデルオブジェクト

        Raises:
            FileNotFoundError: モデルファイルが存在しない場合
            ValueError: model_path が設定されていない場合
        """
        if not self._model_path:
            raise ValueError(f"Model path is not set for result '{self._id}'.")
        path = Path(self._model_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Model file not found: '{self._model_path}'"
            )
        with open(path, "rb") as f:
            # NOTE: pickle.load はデシリアライズ時に任意コードを実行できる形式
            # だが、ここでロードするファイルは必ず同一プロセスが
            # get_tmp_models_dir() 配下に書き出した {uuid}.pkl に限定される
            # ため通常運用でのリスクはない。ただし PC がマルウェアに侵害
            # されている状況では tmpDir への細工により悪用される可能性がある
            # 点は認識しておく。
            return pickle.load(f)

    def delete_model_file(self) -> None:
        """
        保存済みの pickle ファイルを削除する。

        ファイルが存在しない場合はサイレントに無視する。
        """
        if self._model_path:
            path = Path(self._model_path)
            if path.exists():
                path.unlink()
            self._model_path = None

    def has_model_file(self) -> bool:
        """
        モデルファイルが存在するかどうかを返す。

        Returns:
            ファイルが存在する場合 True
        """
        if not self._model_path:
            return False
        return Path(self._model_path).exists()

    def _get_result_type_label(self) -> str:
        """分析種別の表示ラベルを返す。"""
        label_key = _RESULT_TYPE_LABELS.get(self._result_type, "分析結果")
        return _(label_key)

    def _summary_regression(self) -> str | None:
        dep = self._result_data.get("dependentVariable", "")
        model = (self._model_type or "").upper()
        if dep and model:
            return f"{model} / {dep}"
        return dep or None

    def _summary_confidence_interval(self) -> str | None:
        stat = self._result_data.get("statistic", {})
        stat_type = stat.get("type", "") if isinstance(stat, dict) else ""
        level = self._result_data.get("confidenceLevel", "")
        if stat_type and level:
            return f"{stat_type} / {int(float(level) * 100)}%"
        return None

    def _summary_descriptive_statistics(self) -> str | None:
        stats = self._result_data.get("statistics", {})
        if not isinstance(stats, dict):
            return None
        col_count = len(stats)
        first = next(iter(stats.values()), {})
        stat_count = len(first) if isinstance(first, dict) else 0
        if col_count > 0 and stat_count > 0:
            return f"{col_count}列 / {stat_count}統計量"
        return None

    def _summary_did(self) -> str | None:
        dep = self._result_data.get("dependentVariable", "")
        return f"DID / {dep}" if dep else None

    def _summary_rdd(self) -> str | None:
        outcome = self._result_data.get("outcomeVariable", "")
        if outcome:
            return f"RDD / {outcome}"
        cutoff = self._result_data.get("cutoff", "")
        return f"RDD / cutoff={cutoff}" if cutoff != "" else None

    def _build_summary_text(self) -> str:
        """
        フロントエンド一覧表示用の簡潔な説明文を生成する。

        result_type に応じた _summary_* メソッドを呼び出す。
        キーが欠如している場合は description または
        result_type_label にフォールバックする。
        """
        _builders = {
            "regression": self._summary_regression,
            "heckman": self._summary_regression,
            "confidence_interval": self._summary_confidence_interval,
            "descriptive_statistics": (self._summary_descriptive_statistics),
            "did": self._summary_did,
            "rdd": self._summary_rdd,
        }
        builder = _builders.get(self._result_type)
        try:
            text = builder() if builder is not None else None
        except Exception:  # noqa: BLE001
            text = None
        return text or self._description or self._get_result_type_label()

    def to_dict(self) -> dict[str, Any]:
        """
        AnalysisResultを辞書形式に変換
        """
        return {
            "id": self._id,
            "name": self._name,
            "description": self._description,
            "tableName": self._table_name,
            "resultType": self._result_type,
            "resultData": self._result_data,
            "createdAt": self._created_at,
            "modelPath": self._model_path,
            "modelType": self._model_type,
            "entityIdColumn": self._entity_id_column,
            "timeColumn": self._time_column,
        }

    def to_summary_dict(self) -> dict[str, str | None]:
        """
        サマリー情報を辞書形式に変換

        Returns:
            id, name, description, createdAt, tableName,
            resultType, resultTypeLabel, modelType, summaryText
            を含む辞書。modelType は None になる場合がある。
        """
        return {
            "id": self._id,
            "name": self._name,
            "description": self._description,
            "createdAt": self._created_at,
            "tableName": self._table_name,
            "resultType": self._result_type,
            "resultTypeLabel": self._get_result_type_label(),
            "modelType": self._model_type,
            "summaryText": self._build_summary_text(),
        }

import uuid
from datetime import datetime
from typing import Any, Dict


class AnalysisResult:
    """
    分析結果を保持するデータクラス
    """

    _id: str
    _name: str
    _description: str
    _table_name: str
    _regression_output: Dict[str, Any]
    _created_at: str

    def __init__(
        self,
        *,
        name: str,
        description: str,
        table_name: str,
        regression_output: Dict[str, Any],
    ):
        self._id = str(uuid.uuid4())
        self._name = name
        self._description = description
        self._table_name = table_name
        self._regression_output = regression_output
        self._created_at = datetime.now().isoformat()

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
    def regression_output(self) -> Dict[str, Any]:
        return self._regression_output

    @property
    def created_at(self) -> str:
        return self._created_at

    @name.setter
    def name(self, name: str):
        self._name = name

    @description.setter
    def description(self, description: str):
        self._description = description

    def to_dict(self) -> Dict[str, Any]:
        """
        AnalysisResultを辞書形式に変換
        """
        return {
            "id": self._id,
            "name": self._name,
            "description": self._description,
            "tableName": self._table_name,
            "regressionOutput": self._regression_output,
            "createdAt": self._created_at,
        }

    def to_summary_dict(self) -> Dict[str, str]:
        """
        サマリー情報を辞書形式に変換
        """
        return {
            "id": self._id,
            "name": self._name,
            "description": self._description,
            "createdAt": self._created_at,
        }

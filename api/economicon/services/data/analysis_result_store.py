import threading

from economicon.services.data.analysis_result import AnalysisResult


class AnalysisResultStore:
    """
    分析結果をシングルトンで管理するストア
    """

    _instance = None
    _lock: threading.RLock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 初期化が一度だけ行われるようにする
        if not hasattr(self, "_initialized"):
            self._results: dict[str, AnalysisResult] = {}
            self._lock = threading.RLock()
            self._initialized = True

    def save_result(self, result: AnalysisResult) -> str:
        """
        分析結果を保存し、生成されたIDを返す

        Args:
            result: AnalysisResult オブジェクト

        Returns:
            生成された一意のID
        """
        with self._lock:
            self._results[result.id] = result
            return result.id

    def get_result(self, result_id: str) -> AnalysisResult:
        """
        指定されたIDの分析結果を取得

        Args:
            result_id: 結果のID

        Returns:
            AnalysisResult オブジェクト

        Raises:
            KeyError: 指定されたIDの結果が存在しない場合
        """
        with self._lock:
            result = self._results.get(result_id)
            if result:
                return result
            else:
                raise KeyError(
                    f"Analysis result with ID '{result_id}' does not exist."
                )

    def get_all_summaries(self) -> list[dict[str, str]]:
        """
        すべての分析結果のサマリー情報を取得

        Returns:
            サマリー情報のリスト
            (id, name, description, createdAt を含む)
        """
        with self._lock:
            return [
                result.to_summary_dict() for result in self._results.values()
            ]

    def delete_result(self, result_id: str) -> str:
        """
        指定されたIDの分析結果を削除

        合わせて保存済み pickle ファイルも削除する。

        Args:
            result_id: 削除する結果のID

        Returns:
            削除された結果のID

        Raises:
            KeyError: 指定されたIDの結果が存在しない場合
        """
        with self._lock:
            result = self._results.get(result_id)
            if result:
                # pkl ファイルを先に削除してからメモリから除去
                result.delete_model_file()
                del self._results[result_id]
                return result_id
            else:
                raise KeyError(
                    f"Analysis result with ID '{result_id}' does not exist."
                )

    def clear_all(self) -> bool:
        """
        すべての分析結果を削除

        合わせて保存済み pickle ファイルもすべて削除する。

        Returns:
            削除が成功した場合True
        """
        with self._lock:
            for result in self._results.values():
                result.delete_model_file()
            self._results.clear()
            return True

class ValidationError(Exception):
    """
    入力バリデーション専用の例外(全体で統一)
    """

    def __init__(
        self, *, error_code: str, message: str, target: str | None = None
    ):
        self.error_code = error_code
        self.message = message
        self.target = target  # 'table_name', 'column_names' など
        super().__init__(message)


class ProcessingError(Exception):
    """
    バリデーション通過後、実際の処理（計算、解析、ファイル操作等）の最中に
    発生した「実行不能な事態」を示す例外
    """

    def __init__(
        self, *, error_code: str, message: str, detail: str | None = None
    ):
        self.error_code = error_code
        self.message = message
        self.detail = detail  # 技術的な詳細や、スタックトレースの一部など
        super().__init__(message)

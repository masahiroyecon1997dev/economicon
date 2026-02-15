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

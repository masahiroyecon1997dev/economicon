class ApiError(Exception):
    """
    API実行時のエラーを表す例外。
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

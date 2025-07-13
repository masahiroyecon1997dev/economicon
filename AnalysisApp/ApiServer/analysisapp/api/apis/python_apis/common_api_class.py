from abc import abstractmethod, ABC
from typing import Optional, Dict
from ..utilities.validator.common_validators import ValidationError


class AbstractApi(ABC):
    """
    Python APIの抽象クラス。
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def validate(self) -> Optional[ValidationError]:
        pass

    @abstractmethod
    def execute(self) -> Optional[Dict]:
        pass


class ApiError(Exception):
    """
    API実行時のエラーを表す例外。
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

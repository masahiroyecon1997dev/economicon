from abc import abstractmethod, ABC
from typing import Optional, Dict
from ..utils.validator.common_validators import ValidationError


class AbstractApi(ABC):
    """
    Python API縺ｮ謚ｽ雎｡繧ｯ繝ｩ繧ｹ縲・    """

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
    API螳溯｡梧凾縺ｮ繧ｨ繝ｩ繝ｼ繧定｡ｨ縺吩ｾ句､悶・    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

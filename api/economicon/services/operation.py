from typing import Protocol, runtime_checkable

from economicon.utils.validators.common import ValidationError


@runtime_checkable
class DataOperation(Protocol):
    """
    データ操作のProtocolインターフェイス。
    validate()とexecute()メソッドを持つクラスはこのProtocolに適合します。
    """

    def validate(self) -> ValidationError | None:
        """
        操作のバリデーションを実行します。

        Returns:
            ValidationError: バリデーションエラーがある場合
            None: バリデーションが成功した場合
        """
        ...

    def execute(self) -> dict | bytes | None:
        """
        操作を実行します。

        Returns:
            Dict | bytes: 実行結果のデータ
            None: 結果がない場合
        """
        ...


def run_operation(operation: DataOperation) -> dict | bytes | None:
    """
    DataOperationプロトコルに適合するオブジェクトを受け取り、
    validateとexecuteを順次実行します。

    Args:
        operation: DataOperationプロトコルに適合するオブジェクト

    Returns:
        Optional[Dict | bytes]: execute()の実行結果

    Raises:
        ValidationError: バリデーションが失敗した場合
    """
    operation.validate()
    return operation.execute()
    return operation.execute()
    return operation.execute()

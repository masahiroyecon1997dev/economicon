import os
from pathlib import Path

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.utils.exceptions import ValidationError


def _validate_path_base(
    *,
    path_str: str,
    target: str,
    must_be_type: str,  # "file" or "dir"
    mode: int = os.R_OK,
) -> None:
    """ファイルやディレクトリの存在、型、権限を検証する共通関数
    Args:
        path_str: パスの文字列
        target: パラメータ名（例: "filePath"）
        must_be_type:
            "file" か "dir" を指定して、ファイルかディレクトリかを検証
        mode: 権限の種類（デフォルトは読み取り権限 os.R_OK）
    Raises:
        ValidationError: パスが存在しない、型が違う、または権限がない場合

    """
    path = Path(path_str)

    # 存在チェック
    if not path.exists():
        raise ValidationError(
            error_code=ErrorCode.PATH_NOT_FOUND,
            target=target,
            message=_("{} '{}' does not exist.").format(target, path_str),
        )

    # 型チェック (ファイルかディレクトリか)
    if must_be_type == "file" and not path.is_file():
        raise ValidationError(
            error_code=ErrorCode.NOT_A_FILE,
            target=target,
            message=_("{} '{}' is not a file.").format(target, path_str),
        )

    if must_be_type == "dir" and not path.is_dir():
        raise ValidationError(
            error_code=ErrorCode.NOT_A_DIRECTORY,
            target=target,
            message=_("{} '{}' is not a directory.").format(target, path_str),
        )

    # 権限チェック
    if not os.access(path, mode):
        perm = "read" if mode == os.R_OK else "write"
        raise ValidationError(
            error_code=ErrorCode.PERMISSION_DENIED,
            target=target,
            message=_("{} '{}' does not have {} permission.").format(
                target, path_str, perm
            ),
        )


def _validate_file_extension(
    *, path_str: str, target: str, allowed_extensions: list[str]
) -> None:
    """拡張子が許可されたリストに含まれているか検証する
    Args:
        path_str: ファイルパスの文字列
        target: パラメータ名（例: "filePath"）
        allowed_extensions: 許可された拡張子のリスト（例: [".csv", ".json"]）
    Raises:
        ValidationError: 拡張子が許可されていない場合

    """
    ext = Path(path_str).suffix.lower().lstrip(".")  # 例: "csv"
    if ext not in [e.lower().lstrip(".") for e in allowed_extensions]:
        raise ValidationError(
            error_code=ErrorCode.INVALID_FILE_TYPE,
            message=_("{} must be one of the following types: {}.").format(
                target, ", ".join(allowed_extensions)
            ),
            target=target,
        )


def _validate_file_not_empty(*, path_str: str, target: str) -> None:
    """ファイルサイズが0より大きいことを検証する
    Args:
        path_str: ファイルパスの文字列
        target: パラメータ名（例: "filePath"）
    Raises:
        ValidationError: ファイルが空の場合
    """
    if os.path.getsize(path_str) == 0:
        raise ValidationError(
            error_code=ErrorCode.EMPTY_FILE,
            message=_("{} '{}' is empty.").format(target, path_str),
            target=target,
        )


def validate_file_path(
    *, path_str: str, target: str, mode: int = os.R_OK
) -> None:
    """ファイルが存在し、指定された権限があるか検証する

    Args:
        path_str: ファイルパスの文字列
        target: パラメータ名（例: "filePath"）
        mode: 権限の種類（デフォルトは読み取り権限 os.R_OK）

    Raises:
        ValidationError:
                ファイルが存在しない、ファイルでない、または権限がない場合
    """
    _validate_path_base(
        path_str=path_str, target=target, must_be_type="file", mode=mode
    )


def validate_directory_path(
    *, path_str: str, target: str, mode: int = os.R_OK
) -> None:
    """ディレクトリが存在し、指定された権限があるか検証する

    Args:
        path_str: ディレクトリパスの文字列
        target: パラメータ名（例: "directoryPath"）
        mode: 権限の種類（デフォルトは読み取り権限 os.R_OK）

    Raises:
        ValidationError:
            ディレクトリが存在しない、ディレクトリでない、または権限がない場合
    """
    _validate_path_base(
        path_str=path_str, target=target, must_be_type="dir", mode=mode
    )


def validate_file_format(
    *, path_str: str, target: str, allowed_extensions: list[str]
) -> None:
    """拡張子と中身が空でないか検証する

    Args:
        path_str: ファイルパスの文字列
        target: パラメータ名（例: "filePath"）
        allowed_extensions: 許可された拡張子のリスト

    Raises:
        ValidationError: 拡張子が許可されていない場合、またはファイルが空の場合
    """
    _validate_file_extension(
        path_str=path_str, target=target, allowed_extensions=allowed_extensions
    )
    _validate_file_not_empty(path_str=path_str, target=target)

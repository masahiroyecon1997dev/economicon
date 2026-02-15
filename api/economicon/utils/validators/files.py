import os
from pathlib import Path
from typing import List

from economicon.i18n.translation import gettext as _

from .common import (
    ValidationError,
)


def _validate_path_base(
    *,
    path_str: str,
    target: str,
    must_be_type: str,  # "file" or "dir"
    mode: int = os.R_OK,
) -> None:
    path = Path(path_str)

    # 存在チェック
    if not path.exists():
        raise ValidationError(
            error_code="PATH_NOT_FOUND",
            target=target,
            message=_("{} '{}' does not exist.").format(target, path_str),
        )

    # 型チェック (ファイルかディレクトリか)
    if must_be_type == "file" and not path.is_file():
        raise ValidationError(
            error_code="NOT_A_FILE",
            target=target,
            message=_("{} '{}' is not a file.").format(target, path_str),
        )

    if must_be_type == "dir" and not path.is_dir():
        raise ValidationError(
            error_code="NOT_A_DIRECTORY",
            target=target,
            message=_("{} '{}' is not a directory.").format(target, path_str),
        )

    # 権限チェック
    if not os.access(path, mode):
        perm = "read" if mode == os.R_OK else "write"
        raise ValidationError(
            error_code="PERMISSION_DENIED",
            target=target,
            message=_("{} '{}' does not have {} permission.").format(
                target, path_str, perm
            ),
        )


def _validate_file_extension(
    *, path_str: str, target: str, allowed_extensions: List[str]
) -> None:
    """拡張子が許可されたリストに含まれているか検証する"""
    ext = Path(path_str).suffix.lower()  # 例: ".csv"
    if ext not in [e.lower() for e in allowed_extensions]:
        raise ValidationError(
            error_code="INVALID_FILE_TYPE",
            message=_("{} must be one of the following types: {}.").format(
                target, ", ".join(allowed_extensions)
            ),
            target=target,
        )


def _validate_file_not_empty(*, path_str: str, target: str) -> None:
    """ファイルサイズが0より大きいことを検証する"""
    if os.path.getsize(path_str) == 0:
        raise ValidationError(
            error_code="EMPTY_FILE",
            message=_("{} '{}' is empty.").format(target, path_str),
            target=target,
        )


def validate_file_path(
    *, path_str: str, target: str, mode: int = os.R_OK
) -> None:
    """ファイルが存在し、指定された権限があるか検証する"""
    _validate_path_base(
        path_str=path_str, target=target, must_be_type="file", mode=mode
    )


def validate_directory_path(
    *, path_str: str, target: str, mode: int = os.R_OK
) -> None:
    """ディレクトリが存在し、指定された権限があるか検証する"""
    _validate_path_base(
        path_str=path_str, target=target, must_be_type="dir", mode=mode
    )


def validate_file_format(
    *, path_str: str, target: str, allowed_extensions: List[str]
) -> None:
    """拡張子と中身が空でないかをセットでチェックすると便利"""
    _validate_file_extension(
        path_str=path_str, target=target, allowed_extensions=allowed_extensions
    )
    _validate_file_not_empty(path_str=path_str, target=target)

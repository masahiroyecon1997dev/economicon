import os
from pathlib import Path
from typing import List

from economicon.i18n.translation import gettext as _

from ..exceptions import ValidationError


def _validate_path_base(
    *,
    path_str: str,
    target: str,
    must_be_type: str,  # "file" or "dir"
    mode: int = os.R_OK,
) -> None:
    """ファイルやディレクトリの存在、型、権限を検証する共通関数"""
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
    """ファイルが存在し、指定された権限があるか検証する

    Args:
        path_str: ファイルパスの文字列
        target: パラメータ名（例: "filePath"）
        mode: 権限の種類（デフォルトは読み取り権限 os.R_OK）

    Raises:
        ValidationError: ファイルが存在しない、ファイルでない、または権限がない場合
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
        ValidationError: ディレクトリが存在しない、ディレクトリでない、または権限がない場合
    """
    _validate_path_base(
        path_str=path_str, target=target, must_be_type="dir", mode=mode
    )


def validate_file_format(
    *, path_str: str, target: str, allowed_extensions: List[str]
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


def validate_windows_reserved_name(
    *, filename: str, target: str = "filename"
) -> None:
    """
    Windowsで予約されているシステム名（CON, NUL等）がファイル名に使われていないか検証する。
    ※拡張子を除いたベース名部分が対象。
    Args:
        filename: 検証するファイル名
        target: パラメータ名（例: "fileName"）
    Raises:
        ValidationError: 予約された名前が使われている場合
    """
    # 1. 予約名リスト（大文字）
    # COM1-9, LPT1-9, その他システムデバイス名
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    # 2. ファイル名からベース名部分（拡張子なし）を抽出して比較
    # 例: "CON.csv" -> "CON", "aux.json" -> "AUX"
    base_name = os.path.splitext(filename)[0].upper()

    if base_name in reserved_names:
        raise ValidationError(
            error_code="RESERVED_FILENAME",
            message=_(
                "'{}' is a reserved Windows system name and cannot be used as a filename."
            ).format(filename),
            target=target,
        )

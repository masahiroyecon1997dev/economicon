import os
from typing import List, Optional

from .common_validators import (ValidationError,
                                validate_directory_path_exists,
                                validate_file_path_exists,
                                validate_invalid_chars, validate_required,
                                validate_string_length)
from analysisapp.i18n.translation import gettext as _


def validate_file_path(
    file_path: str,
    file_path_param: str
) -> None:
    validate_required(file_path, file_path_param)
    validate_file_path_exists(file_path, file_path_param)


def validate_directory_path(
    directory: str,
    directory_param: str
) -> None:
    validate_required(directory, directory_param)
    validate_directory_path_exists(directory, directory_param)


def validate_directory_path_is_directory(
    directory: str
) -> None:
    if not os.path.isdir(directory):
        message = _("パスがディレクトリではありません: {}").format(directory)
        raise ValidationError(message)


def validate_file_name(
    file_name: str,
    file_name_param: str,
    invalid_chars: Optional[List[str]] = None
) -> None:
    if invalid_chars is None:
        invalid_chars = []
    validate_required(file_name, file_name_param)
    validate_string_length(
        file_name,
        file_name_param,
        min_length=1,
        max_length=255,
    )
    validate_invalid_chars(file_name, file_name_param, invalid_chars)


def validate_separator(
    separator: str,
    separator_param: str
) -> None:
    validate_string_length(
        separator,
        separator_param,
        min_length=1,
        max_length=5,
    )


def validate_sheet_name(
    sheet_name: Optional[str],
    sheet_name_param: str
) -> None:
    if sheet_name is not None:
        validate_string_length(
            sheet_name,
            sheet_name_param,
            min_length=0,
            max_length=255,
        )

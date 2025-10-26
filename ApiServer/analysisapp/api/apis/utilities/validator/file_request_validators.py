from typing import Union
from rest_framework.response import Response
from .file_validator import FileValidator
from .file_validation_config import (TSV_VALIDATOR_CONFIG,
                                     EXCEL_VALIDATOR_CONFIG,
                                     CSV_VALIDATOR_CONFIG,
                                     PARQUET_VALIDATOR_CONFIG)


def validate_tsv_request(request) -> Union[Response, None]:
    """
    TSVファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**TSV_VALIDATOR_CONFIG)
    return validator.validate_request(request)


def validate_excel_request(request) -> Union[Response, None]:
    """
    Excelファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**EXCEL_VALIDATOR_CONFIG)
    return validator.validate_request(request)


def validate_csv_request(request) -> Union[Response, None]:
    """
    CSVファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**CSV_VALIDATOR_CONFIG)
    return validator.validate_request(request)


def validate_parquet_request(request) -> Union[Response, None]:
    """
    Parquetファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**PARQUET_VALIDATOR_CONFIG)
    return validator.validate_request(request)

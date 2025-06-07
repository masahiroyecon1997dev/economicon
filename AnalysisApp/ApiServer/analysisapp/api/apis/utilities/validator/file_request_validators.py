from .file_validators import FileValidator
from .file_validation_config import (TSV_VALIDATOR_CONFIG,
                                     EXCEL_VALIDATOR_CONFIG,
                                     CSV_VALIDATOR_CONFIG,
                                     PARQUET_VALIDATOR_CONFIG)
from typing import Optional, Dict, Any


def validate_tsv_request(request) -> Optional[Dict[str, Any]]:
    """
    TSVファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**TSV_VALIDATOR_CONFIG)
    return validator.validate_request(request)


def validate_excel_request(request) -> Optional[Dict[str, Any]]:
    """
    Excelファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**EXCEL_VALIDATOR_CONFIG)
    return validator.validate_request(request)


def validate_csv_request(request) -> Optional[Dict[str, Any]]:
    """
    CSVファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**CSV_VALIDATOR_CONFIG)
    return validator.validate_request(request)


def validate_parquet_request(request) -> Optional[Dict[str, Any]]:
    """
    Parquetファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**PARQUET_VALIDATOR_CONFIG)
    return validator.validate_request(request)

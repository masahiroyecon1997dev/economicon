from typing import Optional

from fastapi import UploadFile

from .file_validation_config import (CSV_VALIDATOR_CONFIG,
                                     EXCEL_VALIDATOR_CONFIG,
                                     PARQUET_VALIDATOR_CONFIG,
                                     TSV_VALIDATOR_CONFIG)
from .file_validator import FileValidator


async def validate_tsv_request(file: UploadFile) -> Optional[Exception]:
    """
    TSVファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**TSV_VALIDATOR_CONFIG)
    return await validator.validate_file(file)


async def validate_excel_request(file: UploadFile) -> Optional[Exception]:
    """
    Excelファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**EXCEL_VALIDATOR_CONFIG)
    return await validator.validate_file(file)


async def validate_csv_request(file: UploadFile) -> Optional[Exception]:
    """
    CSVファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**CSV_VALIDATOR_CONFIG)
    return await validator.validate_file(file)


async def validate_parquet_request(file: UploadFile) -> Optional[Exception]:
    """
    Parquetファイルアップロードリクエストのバリデーション
    """
    validator = FileValidator(**PARQUET_VALIDATOR_CONFIG)
    return await validator.validate_file(file)
    validator = FileValidator(**PARQUET_VALIDATOR_CONFIG)
    return await validator.validate_file(file)

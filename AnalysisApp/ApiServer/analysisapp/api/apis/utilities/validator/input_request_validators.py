from typing import Optional, Dict, Any
from ..create_response import create_error_response
from rest_framework import status
from .input_validation_config import INPUT_VALIDATOR_CONFIG
from .input_validator import InputValidator
from ...data.tables_info import (TableInfo, all_tables_info)
import re
import json


def validate_add_column_request(request) -> Optional[Dict[str, Any]]:
    """
    テーブルにカラムを追加するリクエストのバリデーション
    """
    validator = InputValidator(INPUT_VALIDATOR_CONFIG)
    return validator.validate_file_name(request)

# def validate_save_file(request):
#     """ファイル保存のバリデーション"""
#     requestData = json.loads(request.body)

#     validator = InputValidator()
#     validator.validate_required(requestData.get('fileName'))

#     # ファイル名に使用できない文字をチェック
#     invalid_chars = r'[<>:"/\\|?*]'
#     if re.search(invalid_chars, value):
#         raise create_error_response(
#             status.HTTP_400_BAD_REQUEST,
#             f"{param_name}に無効な文字が含まれています"
#         )

#     # 拡張子をチェック
#     if allowed_extensions:
#         if not any(value.lower().endswith(ext) for ext in allowed_extensions):
#             raise create_error_response(
#                 status.HTTP_400_BAD_REQUEST,
#                 f"{param_name}は以下の拡張子のいずれかである必要があります: "
#                 f"{allowed_extensions}"
#             )

#         # ファイル名の長さをチェック
#         if len(value) > 255:
#             raise create_error_response(
#                 status.HTTP_400_BAD_REQUEST,
#                 f"{param_name}が長すぎます"
#             )

#         return value


# def validate_table_name(value: str, param_name: str) -> str:
#     """テーブル名のバリデーション"""
#     if not value:
#         raise create_error_response(
#             status.HTTP_400_BAD_REQUEST,
#             f"{param_name}は必須です"
#         )

#     # テーブルが存在するかチェック
#     if value not in tables:
#         available_tables = list(tables.keys())
#         raise create_error_response(
#             status.HTTP_400_BAD_REQUEST,
#             f"指定されたテーブル '{value}' は存在しません。"
#             f"利用可能なテーブル: {available_tables}"
#         )

#     return value

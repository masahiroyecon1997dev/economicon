"""
各ファイルタイプ用の事前定義された設定
"""

# TSVファイル用設定
TSV_VALIDATOR_CONFIG = {
    'max_size': 50 * 1024 * 1024,  # 50MB
    'allowed_extensions': ('.tsv', '.txt'),
    'allowed_mime_types': ['text/tab-separated-values', 'text/plain'],
}

# Excelファイル用設定
EXCEL_VALIDATOR_CONFIG = {
    'max_size': 10 * 1024 * 1024,  # 10MB
    'allowed_extensions': ('.xlsx', '.xls'),
    'allowed_mime_types': [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
    ]
}

# CSVファイル用設定
CSV_VALIDATOR_CONFIG = {
    'max_size': 20 * 1024 * 1024,  # 20MB
    'allowed_extensions': ('.csv',),
    'allowed_mime_types': ['text/csv', 'application/csv']
}

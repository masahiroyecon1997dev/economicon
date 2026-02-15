# テーブルマネジャーのバリデーション設定
TABLES_MANAGER_VALIDATOR_CONFIG = {
    "invalid_chars": r'[<>:"/\\|?*]',
    "table_name_min_length": 1,
    "table_name_max_length": 100,
    "column_name_min_length": 1,
    "column_name_max_length": 100,
}

# フィルタ条件の候補リスト
FILTER_CONDITION_CANDIDATES = [
    "equals",
    "notEquals",
    "greaterThan",
    "lessThan",
    "greaterThanOrEquals",
    "lessThanOrEquals",
]

def validate_path(self, value):
    """パスのバリデーション"""
    if not value:
        raise serializers.ValidationError("パスが空です")

    # 危険な文字列をチェック
    dangerous_patterns = ['..', '~', '$', '|', ';', '&', '`']
    if any(pattern in value for pattern in dangerous_patterns):
        raise serializers.ValidationError("無効な文字が含まれています")

    # 絶対パスかどうかをチェック（必要に応じて）
    try:
        Path(value).resolve()
    except (OSError, ValueError):
        raise serializers.ValidationError("無効なパス形式です")

    return value

def validate_fileName(self, value):
    """ファイル名のバリデーション"""
    if not value:
        raise serializers.ValidationError("ファイル名が空です")

    # ファイル名に使用できない文字をチェック
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, value):
        raise serializers.ValidationError("ファイル名に無効な文字が含まれています")

    # CSV拡張子をチェック
    if not value.lower().endswith('.csv'):
        raise serializers.ValidationError("ファイル名は.csvで終わる必要があります")

    # ファイル名の長さをチェック
    if len(value) > 255:
        raise serializers.ValidationError("ファイル名が長すぎます")

    return value

def validate_tableName(self, value):
    """テーブル名のバリデーション"""
    if not value:
        raise serializers.ValidationError("テーブル名が空です")

    # テーブルが存在するかチェック
    if value not in tables:
        available_tables = list(tables.keys())
        raise serializers.ValidationError(
            f"指定されたテーブル '{value}' は存在しません。"
            f"利用可能なテーブル: {available_tables}"
        )

    return value

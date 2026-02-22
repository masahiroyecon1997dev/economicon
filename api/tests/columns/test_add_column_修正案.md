# test_add_column.py 修正案

## 重要な注意事項

1. **テスト順序**: 正常系テストをファイル上部に配置し、異常系テストをその後に配置
2. **エラーメッセージ**: i18n設定により**日本語メッセージ**が返される前提でテストを記述
3. **テーブル不変性**: 異常系では必ずテーブルが変更されていないことを確認
4. **エラーコード完全一致**: `ErrorCode` Enumを使用して検証
5. **列位置確認**: 正常系では追加された列の位置を検証

## テスト構成（合計38テスト）

### 正常系テスト（13個）

1. 基本的なカラム追加
2. CSV読み込み（ヘッダあり）
3. CSV読み込み（ヘッダなし）
4. 行数不一致（非厳密モード、切り捨て）
5. 行数不一致（非厳密モード、パディング）
6. 境界値テスト（128文字のカラム名：正常）
7. 境界値テスト（1024文字のファイルパス：正常）
8. 境界値テスト（10文字の区切り文字：正常）
9. CSV複数列（1列目のみ使用）
10. 特殊文字を含むカラム名
11. 最初の列の前に追加
12. 最後の列の後に追加
13. 既存データの保持確認

### 異常系テスト（25個）

#### Pydanticバリデーションエラー（422）: 16個

14. 必須フィールド欠如（tableName未指定）
15. 必須フィールド欠如（newColumnName未指定）
16. 必須フィールド欠如（addPositionColumn未指定）
17. 空文字（tableName）
18. 空文字（newColumnName）
19. 空文字（addPositionColumn）
20. 型エラー（tableNameが数値）
21. 型エラー（newColumnNameが数値）
22. 型エラー（addPositionColumnが数値）
23. 文字数超過（newColumnNameが129文字）
24. 文字数超過（csvFilePathが1025文字）
25. 制御文字（newColumnNameに\x00を含む）
26. 制御文字（newColumnNameに\x1fを含む）
27. 制御文字（newColumnNameに\x7fを含む）
28. 区切り文字が空文字
29. 区切り文字が11文字

#### 内部バリデーションエラー（400）: 6個

30. 存在しないテーブル名
31. 既存カラム名と重複
32. 存在しない追加位置カラム
33. CSVファイルが存在しない
34. CSVファイルへのアクセス権がない
35. CSVファイルに列が存在しない

#### 処理エラー（500）: 3個

36. 行数不一致（厳密モード）
37. 空CSVファイル
38. CSV列が存在しない（別パターン）

## 修正が必要な既存テスト

### test_add_column_success

**修正内容**:

- 列の追加位置を確認するアサーションを追加
- 既存データが保持されていることを確認
- レスポンスのresult構造を確認

### test_add_column_from_csv_with_header_success

**修正内容**:

- 列の追加位置を確認するアサーションを追加
- 既存データが保持されていることを確認

### test_add_column_from_csv_without_header_success

**修正内容**:

- 列の追加位置を確認するアサーションを追加
- 既存データが保持されていることを確認

### test_add_column_from_csv_row_count_mismatch_non_strict_truncate

**修正内容**:

- 列の追加位置を確認
- 既存データが保持されていることを確認

### test_add_column_from_csv_row_count_mismatch_non_strict_pad

**修正内容**:

- 列の追加位置を確認
- 既存データが保持されていることを確認

### test_add_column_table_not_found → 削除

**理由**: このテストは「tableName未指定」を意図していたため、422エラーを期待すべき。新規テスト `test_add_column_missing_table_name` に置き換え

### test_add_column_invalid_table

**修正内容**:

- エラーコード `DATA_NOT_FOUND` の確認
- メッセージ完全一致（日本語）: `"tableName 'NoTable'は存在しません。"`
- テーブルが変更されていないことを確認

### test_add_column_duplicate_name

**修正内容**:

- エラーコード `DATA_ALREADY_EXISTS` の確認
- メッセージ完全一致（日本語）: `"newColumnName 'A'は既に存在します。"`
- テーブルが変更されていないことを確認

### test_add_column_invalid_position_column

**修正内容**:

- エラーコード `DATA_NOT_FOUND` の確認
- メッセージ完全一致（日本語）: `"addPositionColumn 'Z'は存在しません。"`
- テーブルが変更されていないことを確認

### test_add_column_from_csv_row_count_mismatch_strict

**修正内容**:

- エラーコード `ROW_COUNT_MISMATCH` の確認
- メッセージの検証を具体的に（日本語、行数"5"と"3"を含む）
- テーブルが変更されていないことを確認

### test_add_column_from_csv_file_not_found

**修正内容**:

- エラーコード `PATH_NOT_FOUND` の確認
- 日本語メッセージの確認
- テーブルが変更されていないことを確認

### test_add_column_from_csv_empty_file

**修正内容**:

- エラーコード `EMPTY_CSV_FILE` の確認
- 日本語メッセージ確認（"空"または"empty"を含む）
- テーブルが変更されていないことを確認

## 追加すべき新規テスト

### 正常系（境界値・エッジケース）

#### test_add_column_new_column_name_max_length

**内容**: 新カラム名がちょうど128文字の場合（正常系）
**検証**: 128文字のカラム名で正常に追加できる、列位置が正しい

#### test_add_column_csv_file_path_max_length

**内容**: CSVファイルパスがちょうど1024文字の場合（正常系）
**検証**: 1024文字のパスで正常に読み込める

#### test_add_column_separator_max_length

**内容**: 区切り文字がちょうど10文字の場合（正常系）
**検証**: 10文字の区切り文字で正常に動作

#### test_add_column_special_chars_in_column_name

**内容**: 新カラム名に特殊文字（日本語、絵文字、記号など）が含まれる場合（正常系）
**検証**: `"カラム名😀"`, `"col@#$%"` などが正常に追加できる

#### test_add_column_csv_with_multiple_columns

**内容**: CSVファイルに複数列があるが、1列目のみ使用される（正常系）
**検証**: 複数列CSVから1列目だけが取得される

#### test_add_column_first_position

**内容**: 最初の列の直後に追加する場合
**注意**: `addPositionColumn`は「この列の後に追加」なので、Aの後に追加すると`["A", "C", "B"]`になる
**検証**: 列順が正しい

#### test_add_column_last_position

**内容**: 最後の列の直後に追加する場合
**検証**: Bの後に追加すると`["A", "B", "C"]`になる

#### test_add_column_preserves_other_columns_data

**内容**: 列追加時に他の列のデータが完全に保持されていることを確認（正常系）
**検証**: 全ての既存列のデータ、型、順序が保持される

### 異常系（Pydanticバリデーション: 422）

#### test_add_column_missing_table_name

**内容**: テーブル名が未指定の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_missing_new_column_name

**内容**: 新カラム名が未指定の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_missing_add_position_column

**内容**: 追加位置カラムが未指定の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_empty_table_name

**内容**: テーブル名が空文字の場合（`"tableName": "   "`→strip後に空）
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_empty_new_column_name

**内容**: 新カラム名が空文字の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_empty_add_position_column

**内容**: 追加位置カラムが空文字の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_table_name_is_number

**内容**: テーブル名が数値の場合（`"tableName": 123`）
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_new_column_name_is_number

**内容**: 新カラム名が数値の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_add_position_column_is_number

**内容**: 追加位置カラムが数値の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_new_column_name_too_long

**内容**: 新カラム名が129文字の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_csv_file_path_too_long

**内容**: CSVファイルパスが1025文字の場合
**検証**: 422エラー、VALIDATION_ERROR、details存在、テーブル不変

#### test_add_column_new_column_name_with_null_char

**内容**: 新カラム名にNull文字(\x00)が含まれる場合
**検証**: 422エラー、VALIDATION_ERROR、パターンマッチエラー、テーブル不変

#### test_add_column_new_column_name_with_control_char_1f

**内容**: 新カラム名に制御文字(\x1f)が含まれる場合
**検証**: 422エラー、VALIDATION_ERROR、パターンマッチエラー、テーブル不変

#### test_add_column_new_column_name_with_control_char_7f

**内容**: 新カラム名に制御文字(\x7f、DEL)が含まれる場合
**検証**: 422エラー、VALIDATION_ERROR、パターンマッチエラー、テーブル不変

#### test_add_column_separator_empty

**内容**: 区切り文字が空文字の場合
**検証**: 422エラー、VALIDATION_ERROR、min_length=1違反、テーブル不変

#### test_add_column_separator_too_long

**内容**: 区切り文字が11文字の場合
**検証**: 422エラー、VALIDATION_ERROR、max_length=10違反、テーブル不変

### 異常系（内部バリデーション: 400）

#### test_add_column_csv_file_permission_denied

**内容**: CSVファイルへのアクセス権がない場合
**実装方法**:

- Windowsの場合: ファイル作成後に`os.chmod(csv_path, 0o000)`で権限削除
- または読み取り専用ディレクトリを使用
  **検証**: 400エラー、PERMISSION_DENIED、日本語メッセージ、テーブル不変

#### test_add_column_csv_no_columns

**内容**: CSVファイルに列が存在しない場合（widthが0）
**実装方法**: ヘッダなしで完全に空のCSVファイルを作成
**検証**: 500エラー、NO_COLUMNS_IN_CSV_FILE、日本語メッセージ、テーブル不変

## 実装サンプル

### 正常系の例

```python
def test_add_column_new_column_name_max_length(client, tables_store):
    """新カラム名がちょうど128文字の場合（正常系）"""
    long_name = "a" * 128  # ちょうど128文字

    payload = {
        "tableName": "TestTable",
        "newColumnName": long_name,
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == long_name

    # 列が正しく追加されている
    df_after = tables_store.get_table("TestTable").table
    assert long_name in df_after.columns
    assert df_after.columns == ["A", long_name, "B"]
```

### 異常系の例（Pydantic - 空文字）

```python
def test_add_column_empty_table_name(client, tables_store):
    """テーブル名が空文字の場合（strip後）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    payload = {
        "tableName": "   ",  # スペースのみ → strip後に空文字
        "newColumnName": "C",
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "NG"
    assert response_data["errorCode"] == ErrorCode.VALIDATION_ERROR
    assert "details" in response_data
    assert len(response_data["details"]) > 0
    # detailsの中に「tableName」や「必須」などの文言が含まれることを確認
    assert any("tableName" in str(detail) or "テーブル名" in str(detail)
               for detail in response_data["details"])

    # テーブルが変更されていない
    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)
```

### 異常系の例（Pydantic - 型エラー）

```python
def test_add_column_table_name_is_number(client, tables_store):
    """テーブル名が数値の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    payload = {
        "tableName": 123,  # 数値（文字列でない）
        "newColumnName": "C",
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == "NG"
    assert response_data["errorCode"] == ErrorCode.VALIDATION_ERROR
    assert "details" in response_data
    assert len(response_data["details"]) > 0
    # 型エラーのメッセージ確認
    assert any("string" in str(detail).lower() or "文字列" in str(detail)
               for detail in response_data["details"])

    # テーブルが変更されていない
    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)
```

### 異常系の例（内部バリデーション - 日本語メッセージ）

```python
def test_add_column_invalid_table(client, tables_store):
    """存在しないテーブル名"""
    df_before = tables_store.get_table("TestTable").table.clone()

    payload = {
        "tableName": "NoTable",
        "newColumnName": "C",
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert response_data["errorCode"] == ErrorCode.DATA_NOT_FOUND
    # 日本語メッセージを期待
    assert response_data["message"] == "tableName 'NoTable'は存在しません。"

    # テーブルが変更されていない
    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)
```

### 異常系の例（アクセス権）

```python
def test_add_column_csv_file_permission_denied(client, tables_store):
    """CSVファイルへのアクセス権がない場合"""
    import stat

    df_before = tables_store.get_table("TestTable").table.clone()

    # 一時CSVファイルを作成
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n10\n20\n30\n")
        csv_path = tmpfile.name

    try:
        # 読み取り権限を削除（Windows: 読み取り専用に設定して、さらに読み取りも不可に）
        os.chmod(csv_path, stat.S_IWRITE)  # 書き込みのみ許可（read不可）

        payload = {
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "A",
            "csvFilePath": csv_path,
            "csvHasHeader": True,
        }
        response = client.post("/api/column/add", json=payload)

        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data["code"] == "NG"
        assert response_data["errorCode"] == ErrorCode.PERMISSION_DENIED
        # 日本語メッセージ確認
        assert "権限" in response_data["message"] or "アクセス" in response_data["message"]

        # テーブルが変更されていない
        df_after = tables_store.get_table("TestTable").table
        assert df_after.equals(df_before)
    finally:
        # 権限を戻してから削除
        os.chmod(csv_path, stat.S_IWRITE | stat.S_IREAD)
        os.unlink(csv_path)
```

## メッセージ検証の注意点

日本語メッセージが返されるため、以下のパターンで検証：

```python
# 完全一致（推奨 - 内部バリデーション）
assert response_data["message"] == "tableName 'NoTable'は存在しません。"

# 部分一致（Pydanticエラーなど、フォーマットが変わる可能性がある場合）
assert "NoTable" in response_data["message"]
assert "存在" in response_data["message"]

# detailsの確認（Pydanticエラー）
assert "details" in response_data
assert len(response_data["details"]) > 0
assert any("必須" in str(detail) or "required" in str(detail).lower()
           for detail in response_data["details"])
```

## 実装の優先順位

1. **最優先**: 既存テストの修正（12個）- まずこれらを動作させる
2. **高優先**: Pydanticバリデーション異常系（16個）- バリデーションの網羅性向上
3. **中優先**: 内部バリデーション異常系（3個追加）- エッジケース対応
4. **低優先**: 正常系のエッジケース（5個追加）- 境界値テスト

## チェックリスト

- [ ] 正常系テストがファイル上部に配置されている
- [ ] 異常系テストがファイル下部に配置されている
- [ ] 全ての異常系テストでテーブル不変性を確認している
- [ ] エラーコードに`ErrorCode`Enumを使用している
- [ ] 日本語メッセージを前提にしている
- [ ] Pydanticエラーで`details`を確認している
- [ ] 正常系で列位置を確認している
- [ ] 境界値テスト（128文字、1024文字、10文字）を実装している
- [ ] 空文字テストを実装している
- [ ] 型エラーテストを実装している
- [ ] CSVアクセス権のテストを実装している

# Backend Spec

## 目的

バックエンド API の設計仕様と未解消の実装課題を管理する。

## 運用ルール

- 未実装・未修正の項目だけを記載する。
- 実装完了を確認した項目はこの文書から削除する。
- フロントエンドに影響する API 変更は `docs/spec/frontend-spec.md` と合わせて管理する。

---

## 診断列データ永続化: pickle 廃止 → numpy BLOB / SQLite 移行（Option A）

pickle による `AnalysisResult.save_model()` / `load_model()` を廃止し、診断配列を SQLite BLOB として保存する方式に移行する。

> **現状**: pickle 保存を一時停止済み（`save_model()` は no-op）。
> `add-diagnostic-columns` エンドポイントは `MODEL_FILE_NOT_FOUND` を返す一時停止状態。
> 関連テストは `@pytest.mark.skip` で一時無効化済み。

### 背景・目的

- `pickle.load` は任意コード実行可能なフォーマット。将来のデータ共有機能でリスクが顕在化する
- `numpy.load(.npz)` は数値配列のみを扱うため任意コード実行不可（安全）
- SQLite BLOB に保存することで永続化・セッション再起動後の利用も可能にする

### 実装対象ファイル

| ファイル                                                         | 変更内容                                                                        |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `api/economicon/services/data/analysis_result.py`                | `save_model` / `load_model` / `get_tmp_models_dir` を診断配列 I/O に置き換え    |
| `api/economicon/services/data/analysis_result_store.py`          | `save_diagnostic_arrays()` / `load_diagnostic_arrays()` を追加（SQLite 永続化） |
| `api/economicon/services/regressions/estimators/_base.py`        | 推定後に `diagnostics.py` 関数を呼び出して配列を保存                            |
| `api/economicon/services/selection_models/heckman_regression.py` | 同上（step1/step2 両段階の診断配列を保存）                                      |
| `api/economicon/services/regressions/add_diagnostic_columns.py`  | `load_model()` の代わりに `load_diagnostic_arrays()` を使用                     |

### 保存データ構造 `DiagnosticArrays`

推定直後に `diagnostics.py` 関数から抽出し、`numpy.savez_compressed` で BytesIO にシリアライズして SQLite BLOB に格納する。

| フィールド     | 型                   | 内容                                                 |
| -------------- | -------------------- | ---------------------------------------------------- |
| `fittedvalues` | `np.ndarray`         | 予測値（latent or observable、モデル種別に応じた値） |
| `resid`        | `np.ndarray \| None` | 残差（`resid_dev` / `resid_response` を含む）        |
| `resid_std`    | `np.ndarray \| None` | 標準化残差（OLS のみ）                               |
| `ci_lower_95`  | `np.ndarray \| None` | 予測値 95% CI 下限（OLS のみ）                       |
| `ci_upper_95`  | `np.ndarray \| None` | 予測値 95% CI 上限（OLS のみ）                       |
| `row_indices`  | `np.ndarray`         | 元テーブルの 0-based 行インデックス（欠損除去後）    |

### 保存・読み込みフロー

```
推定時 (_base.py / heckman_regression.py):
  diagnostics.py 関数を呼び出す → DiagnosticArrays 生成
  → numpy.savez_compressed(BytesIO) → BLOB
  → analysis_result_store.save_diagnostic_arrays(result_id, blob)

診断列追加時 (add_diagnostic_columns.py):
  analysis_result_store.load_diagnostic_arrays(result_id)
  → numpy.load(BytesIO) → DiagnosticArrays
  → Polars Series に変換 → テーブルに left_join → 保存
```

### SQLite スキーマ

```sql
CREATE TABLE IF NOT EXISTS diagnostic_arrays (
    result_id  TEXT PRIMARY KEY,
    data       BLOB NOT NULL,
    created_at TEXT NOT NULL
);
```

- ファイルパス: `get_tmp_models_dir()` 配下の `diagnostic_arrays.db`
- `numpy.load()` は `allow_pickle=False` で呼び出すこと（安全のため）

### セキュリティ要件

- `numpy.load(allow_pickle=False)` を必ず指定する
- DB ファイルは `%LOCALAPPDATA%/economicon/tmp/models/` に固定し、パスをハードコードしない
- SQLite ファイルへのユーザー入力パスは受け付けない（`result_id` は UUID のみ許可）

### テスト再有効化条件

`api/tests/regressions/test_add_diagnostic_columns.py` および `api/tests/selection_models/heckman/test_heckman.py` の `@pytest.mark.skip` を外す。

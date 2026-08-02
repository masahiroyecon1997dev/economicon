# Backend Spec

Economicon バックエンド API（FastAPI Python サイドカー）の設計仕様書。
Claude Code などの AI エージェントがコード生成・レビュー・変更を行う際の参照ドキュメント。

---

## 1. アーキテクチャ概要

| 項目              | 内容                                                                                                              |
| ----------------- | ----------------------------------------------------------------------------------------------------------------- |
| 構成              | FastAPI Python サイドカー + React 19 / Tauri 2                                                                    |
| 通信              | Tauri `invoke` のみ（フロントから HTTP fetch 禁止）                                                               |
| ポート            | `ECONOMICOM_API_PORT` 環境変数で決定（デフォルト 8000）                                                           |
| CORS 許可オリジン | `tauri://localhost`（Windows/Linux）, `https://tauri.localhost`（macOS）, 開発時のみ `VITE_DEV_SERVER_URL` も追加 |

### ライフサイクル

```
起動時: SettingsStore.load_settings() → TablesStore 初期化
        → AnalysisResultStore.clear_all()（孤立 pkl 削除）
終了時: TablesStore.clear_tables()
        → AnalysisResultStore.clear_all()
        → SettingsStore（設定をファイルに書き込み）
```

---

## 2. 技術スタック

| 種別           | ライブラリ                                                       |
| -------------- | ---------------------------------------------------------------- |
| フレームワーク | FastAPI（Python 3.14+）                                          |
| パッケージ管理 | `uv`                                                             |
| リント         | `ruff`（行長 79、isort、flake8-bugbear、pyupgrade）              |
| データ処理     | **Polars 優先**（Pandas は statsmodels/linearmodels 連携時のみ） |
| スキーマ検証   | Pydantic v2（strict モード・camelCase エイリアス）               |
| 統計           | statsmodels, linearmodels, scipy, numpy                          |
| i18n           | fastapi-babel（ContextVar ベース・スレッドセーフ）               |
| テスト         | pytest + pytest-cov                                              |

---

## 3. 設計原則

### 3.1 DataOperation プロトコル

全サービスクラスが実装する構造的部分型（継承不要）。

```python
class DataOperation(Protocol):
    def validate(self) -> ValidationError | None: ...
    def execute(self) -> dict | bytes | None: ...
```

`run_operation(op)` が `validate()` → `execute()` の順に呼び出す。
`validate()` がエラーを送出した場合 `execute()` は呼ばれない。

- **`validate()`**: ビジネスルール検証（テーブル存在確認・列名チェックなど）。失敗時は `ValidationError` を raise。
- **`execute()`**: Polars ロジック実行。処理エラーは `ProcessingError`（旧 `ApiError`）を raise。
- データ読み書きは必ず `TablesStore` / `AnalysisResultStore` / `SettingsStore` 経由。

### 3.2 データ不変性

テーブル操作は**元テーブルを上書きせず新テーブルを生成**する。
既存テーブルの変更を要する操作（列追加・列削除など）は、新 DataFrame を生成して同名テーブルに上書き登録する。

### 3.3 i18n

ユーザー向け文字列（エラーメッセージ・ラベル）は必ず `_()` でラップする。
JSX 内の日本語ハードコード禁止（フロントは `t("Key")` を使用）。

---

## 4. レスポンスフォーマット

### 成功レスポンス

```json
{
  "code": "OK",
  "result": {
    /* 操作固有のフィールド */
  }
}
```

### エラーレスポンス

```json
{
  "code": "ERROR_CODE",
  "message": "ユーザー向けメッセージ",
  "details": ["詳細1", "詳細2"] // バリデーションエラー時のみ
}
```

### HTTP ステータスコード対応表

| 例外                                | HTTP | エラーコード       |
| ----------------------------------- | ---- | ------------------ |
| `RequestValidationError` (Pydantic) | 422  | `VALIDATION_ERROR` |
| `ValidationError`（ビジネスルール） | 400  | 操作固有コード     |
| `ValueError`                        | 400  | `VALUE_ERROR`      |
| `ProcessingError`                   | 500  | 操作固有コード     |
| `NotImplementedError`               | 501  | `NOT_IMPLEMENTED`  |
| `KeyError`                          | 404  | `RESULT_NOT_FOUND` |
| その他 `Exception`                  | 500  | `UNEXPECTED_ERROR` |

---

## 5. インメモリストア

### TablesStore

Polars `DataFrame` をキー（テーブル名）でメモリ管理。永続化なし。
アプリ終了時にクリア。

### AnalysisResultStore

分析結果（係数・統計量など）をインメモリ辞書で管理。
アプリ終了時にクリア。

> **[TODO] pickle → SQLite BLOB 移行**: 現在 `save_model()` は no-op。`add-diagnostic-columns` は `MODEL_FILE_NOT_FOUND` を返す一時停止状態。詳細は §10 参照。

### SettingsStore

設定（言語・テーマ・パスなど）を JSON ファイルから読み込み、
アプリ終了時に一括書き込み。パス: `%LOCALAPPDATA%/economicon/settings.json`

---

## 6. スキーマ規約

### BaseRequest（リクエスト共通）

```python
model_config = ConfigDict(
    alias_generator=to_camel,  # snake_case → camelCase
    populate_by_name=True,
    from_attributes=True,
    strict=True,               # 型の暗黙変換禁止
)
```

### 型エイリアス（`schemas/types.py`）

| 型              | 制約                                                                           |
| --------------- | ------------------------------------------------------------------------------ |
| `TableName`     | 空白トリム・1文字以上                                                          |
| `NewTableName`  | TableName 制約 + Windows 予約名禁止 + 先頭ドット禁止 + 末尾スペース/ドット禁止 |
| `ColumnName`    | 空白トリム・1文字以上                                                          |
| `NewColumnName` | ColumnName 制約 + NUL 文字禁止                                                 |
| `FilePath`      | 絶対パス・存在確認                                                             |
| `DirectoryPath` | 絶対パス・ディレクトリ存在確認                                                 |

---

## 7. エンドポイント一覧

### 7.1 データ I/O（`/data`）

| メソッド | パス           | 概要                                        |
| -------- | -------------- | ------------------------------------------- |
| POST     | `/data/import` | ファイルインポート（CSV/TSV/Excel/Parquet） |
| POST     | `/data/export` | ファイルエクスポート（csv/excel/parquet）   |

**`POST /data/import` リクエスト**

```json
{
  "filePath": "/absolute/path/to/file.csv",
  "tableName": "my_table",
  "separator": ",",
  "encoding": "utf8",
  "sheetName": null
}
```

- `separator`: カンマ/タブ/任意1〜10文字（CSV/TSV のみ有効）
- `encoding`: `utf8` / `latin1` / `ascii` / `gbk` / `windows-1252` / `shift_jis`
- `sheetName`: Excel のみ有効。null = 先頭シート
- インポート後 `last_opened_path` をメモリ上の設定に反映

**`POST /data/export` リクエスト**

```json
{
  "tableName": "my_table",
  "directoryPath": "/absolute/output/dir",
  "fileName": "output",
  "format": "csv",
  "separator": ",",
  "encoding": "utf8",
  "includeHeader": true,
  "sheetName": null
}
```

- `format`: `csv` / `excel` / `parquet`
- 拡張子は `format` に応じて自動付与
- エクスポート後 `last_opened_path` をメモリ上の設定に反映

---

### 7.2 テーブル操作（`/table`）

| メソッド | パス                            | 概要                                        |
| -------- | ------------------------------- | ------------------------------------------- |
| POST     | `/table/get-list`               | テーブル一覧取得                            |
| POST     | `/table/rename`                 | テーブル名変更                              |
| POST     | `/table/delete`                 | テーブル削除                                |
| POST     | `/table/duplicate`              | テーブル複製                                |
| POST     | `/table/clear`                  | 全テーブル削除                              |
| POST     | `/table/fetch-to-json`          | テーブルデータ取得（JSON）                  |
| POST     | `/table/fetch-to-arrow`         | テーブルデータ取得（Apache Arrow バイナリ） |
| POST     | `/table/fetch-plot-data`        | プロット用データ取得（Arrow バイナリ）      |
| POST     | `/table/filter`                 | フィルタ適用（新テーブル生成）              |
| POST     | `/table/create-join`            | 結合テーブル作成                            |
| POST     | `/table/create-union`           | ユニオンテーブル作成                        |
| POST     | `/table/create-simulation-data` | シミュレーションデータテーブル作成          |

**結合種別** (`JoinType`): `inner` / `left` / `right` / `full`

**フィルタ演算子** (`FilterOperatorType`):
`equals` / `notEquals` / `greaterThan` / `lessThan` / `greaterThanOrEquals` / `lessThanOrEquals`

**論理演算子** (`LogicalOperatorType`): `and` / `or`

---

### 7.3 列操作（`/column`）

| メソッド | パス                     | 概要                         |
| -------- | ------------------------ | ---------------------------- |
| POST     | `/column/get-list`       | 列一覧取得                   |
| POST     | `/column/delete`         | 列削除                       |
| POST     | `/column/rename`         | 列名変更                     |
| POST     | `/column/move`           | 列移動（順序変更）           |
| POST     | `/column/sort`           | 列並び替え                   |
| POST     | `/column/cast`           | 型変換                       |
| POST     | `/column/calculate`      | 計算列追加（Polars 式）      |
| POST     | `/column/transform`      | 変換列追加（log/power/root） |
| POST     | `/column/add-dummy`      | ダミー変数列追加             |
| POST     | `/column/add-lag-lead`   | ラグ・リード列追加           |
| POST     | `/column/add-simulation` | シミュレーション列追加       |
| POST     | `/column/add-panel-time` | パネル時点列追加             |

**計算式（`/column/calculate`）**: Polars 式構文。
例: `pl.col("price") * pl.col("quantity")`
AST レベルで構文チェック済み（422 で早期返却）。

**変換種別** (`TransformMethodType`): `log` / `power` / `root`

**ダミーモード** (`DummyMode`):

- `single`: 指定カテゴリに対応する 0/1 列を 1 本追加
- `all_except_base`: ベースカテゴリを除く全カテゴリに 1 本ずつ追加

---

### 7.4 統計分析（`/statistics`）

| メソッド | パス                                        | 概要                     |
| -------- | ------------------------------------------- | ------------------------ |
| POST     | `/statistics/confidence-interval`           | 信頼区間計算             |
| POST     | `/statistics/descriptive`                   | 記述統計                 |
| POST     | `/statistics/create-correlation-table`      | 相関行列テーブル作成     |
| POST     | `/statistics/test`                          | 統計的検定               |
| POST     | `/statistics/create-group-statistics-table` | GroupBy 統計テーブル作成 |

**信頼区間統計量種別** (`ConfidenceIntervalStatisticsType`):
`mean` / `median`（Bootstrap） / `proportion` / `variance` / `standard_deviation`

**記述統計量** (`DescriptiveStatisticType`):
`mean` / `median` / `mode` / `variance` / `std_dev` / `range` / `iqr` / `count` / `null_count` / `null_ratio` / `population_variance` / `min` / `max` / `skewness` / `kurtosis`

**検定種別** (`StatisticalTestType`): `t-test` / `z-test` / `f-test`
**対立仮説** (`AlternativeHypothesis`): `two-sided` / `larger` / `smaller`

**相関係数法** (`CorrelationMethod`): `pearson` / `spearman` / `kendall`
**欠損値処理** (`MissingHandlingMethod`): `pairwise` / `listwise`

統計・信頼区間・検定の各エンドポイントは `resultId`（UUID）を返し、
詳細は `GET /analysis/results/{resultId}` で取得する。

---

### 7.5 回帰分析（`/analysis`）

#### `POST /analysis/regression`（統合エンドポイント）

```json
{
  "tableName": "my_table",
  "resultName": "OLS モデル 1",
  "description": "メモ",
  "dependentVariable": "y",
  "explanatoryVariables": ["x1", "x2"],
  "hasConst": true,
  "missingValueHandling": "remove",
  "analysis": { "method": "ols" },
  "standardError": { "method": "nonrobust" }
}
```

**`analysis` のディスクリミネータフィールド: `method`**

| method   | クラス                        | 追加パラメータ                                                                                     |
| -------- | ----------------------------- | -------------------------------------------------------------------------------------------------- |
| `ols`    | `OLSParams`                   | なし                                                                                               |
| `logit`  | `LogitParams`                 | `regularization?`, `calculateMarginalEffects`, `binaryResidualType`                                |
| `probit` | `ProbitParams`                | 同上                                                                                               |
| `tobit`  | `TobitParams`                 | `leftCensoringLimit`, `rightCensoringLimit`                                                        |
| `fe`     | `FEParams`                    | `entityIdColumn`, `timeColumn?`                                                                    |
| `re`     | `REParams`                    | `entityIdColumn`, `timeColumn?`                                                                    |
| `iv`     | `InstrumentalVariablesParams` | `ivMethod`（2sls/gmm）, `instrumentalVariables`, `endogenousVariables`, `gmmWeightMatrix`          |
| `feiv`   | `PanelIvParams`               | `entityIdColumn`, `timeColumn?`, `instrumentalVariables`, `endogenousVariables`, `gmmWeightMatrix` |
| `lasso`  | `LassoParams`                 | `alpha`, `alphaConvention`, `maxIter`, `calculateSe`, `bootstrapIterations`, `randomState`         |
| `ridge`  | `RidgeParams`                 | 同上                                                                                               |
| `wls`    | `WLSParams`                   | `weightsColumn`                                                                                    |
| `gls`    | `GLSParams`                   | `sigmaTableName`（n×n 正定値行列テーブル）                                                         |
| `fgls`   | `FGLSParams`                  | `fglsMethod`（heteroskedastic/ar1）, `maxIter`                                                     |

**識別条件バリデーション（IV/FEIV）**:
`instrumentalVariables` の数 ≥ `endogenousVariables` の数（劣識別は 400 エラー）。

**`standardError` のディスクリミネータフィールド: `method`**

| method      | 追加パラメータ                                              |
| ----------- | ----------------------------------------------------------- |
| `nonrobust` | なし                                                        |
| `robust`    | `hcType`（HC0/HC1/HC2/HC3、デフォルト HC1）                 |
| `cluster`   | `groups`（クラスター列名リスト）, `useCorrection`           |
| `hac`       | `maxlags`, `kernel`（デフォルト bartlett）, `useCorrection` |

**`missingValueHandling`**: `remove`（デフォルト） / `ignore` / `error`

**レスポンス**: `{ "resultId": "<uuid>" }`
詳細は `GET /analysis/results/{resultId}` で取得。

---

#### `POST /analysis/regression/add-diagnostic-columns`

推定済みモデルから予測値・残差・信頼区間を元テーブルに列追加する。

```json
{
  "tableName": "my_table",
  "resultId": "<uuid>",
  "target": "both",
  "standardized": false,
  "includeInterval": false,
  "feType": "total"
}
```

| パラメータ        | 型                                   | 説明                                                             |
| ----------------- | ------------------------------------ | ---------------------------------------------------------------- |
| `target`          | `"fitted"` / `"residual"` / `"both"` | 追加する診断列の種類                                             |
| `standardized`    | bool                                 | 標準化残差を含めるか（OLS 系のみ有効）                           |
| `includeInterval` | bool                                 | 95% 予測区間を含めるか（OLS のみ有効）                           |
| `feType`          | `"total"` / `"within"`               | FE/RE のみ有効。`total`=全体予測値、`within`=within 変換後予測値 |

> **[TODO]** 現在 `MODEL_FILE_NOT_FOUND` を返す一時停止状態（pickle 廃止対応中）。詳細は §10 参照。

---

#### `POST /analysis/heckman-regression`

サンプルセレクションバイアスを Heckman 2 段階推定で補正する。

```json
{
  "tableName": "my_table",
  "resultName": "Heckman モデル",
  "description": "",
  "dependentVariable": "y",
  "explanatoryVariables": ["x1", "x2"],
  "selectionColumn": "selected",
  "selectionVariables": ["x1", "x2", "z"],
  "hasConst": true,
  "missingValueHandling": "remove",
  "reportFirstStage": true
}
```

- Step 1: Probit（選択方程式） → 逆ミルズ比（IMR）を計算
- Step 2: OLS（結果方程式、IMR を追加）
- **識別条件バリデーション**: `selectionVariables` が `explanatoryVariables` にない変数を 1 つ以上含む必要あり（除外制約）

**レスポンス**: `{ "resultId": "<uuid>" }`

---

#### `POST /analysis/did`

TWFE（Two-Way Fixed Effects）に基づく差の差（DID）推定。

```json
{
  "tableName": "my_table",
  "resultName": "DID 分析",
  "description": "",
  "dependentVariable": "y",
  "explanatoryVariables": [],
  "treatmentColumn": "treated",
  "postColumn": "post",
  "timeColumn": "year",
  "entityIdColumn": "entity_id",
  "includeEventStudy": false,
  "basePeriod": null,
  "maxPrePeriods": null,
  "maxPostPeriods": null,
  "missingValueHandling": "remove",
  "standardError": {
    "method": "cluster",
    "groups": ["entity_id"],
    "useCorrection": true
  },
  "confidenceLevel": 0.95
}
```

- 交差項（`treated × post`）はサービス層で自動生成
- `includeEventStudy=true` 時: 各時点の処置効果係数 δ_k を推定
- `basePeriod=null` 時: 処置直前期（通常 -1）を自動選択
- `basePeriod` / `maxPrePeriods` / `maxPostPeriods` は `includeEventStudy=false` のとき設定不可（400 エラー）
- **推奨**: 標準誤差は個体レベルのクラスタ標準誤差

**レスポンス**: `{ "resultId": "<uuid>" }`

---

#### `POST /analysis/rdd`（501 Not Implemented）

回帰不連続デザイン分析。
`rdrobust` / `rddensity` は GPL ライセンスのため削除済み。現在は常に 501 を返す。

---

### 7.6 分析結果管理（`/analysis/results`）

| メソッド | パス                            | 概要                                                             |
| -------- | ------------------------------- | ---------------------------------------------------------------- |
| GET      | `/analysis/results`             | 全分析結果サマリー一覧取得                                       |
| GET      | `/analysis/results/{result_id}` | 分析結果詳細取得                                                 |
| PATCH    | `/analysis/results/{result_id}` | メタデータ更新（`name` / `description` / `summaryTextOverride`） |
| DELETE   | `/analysis/results/{result_id}` | 分析結果削除                                                     |
| DELETE   | `/analysis/results`             | 全分析結果削除                                                   |
| POST     | `/analysis/results/output`      | 推定結果をテキスト/Markdown/LaTeX 形式で整形出力                 |

**`AnalysisResultSummary` フィールド**

| フィールド        | 型             | 内容                                                                                                          |
| ----------------- | -------------- | ------------------------------------------------------------------------------------------------------------- |
| `id`              | string         | UUID                                                                                                          |
| `name`            | string         | 分析結果名                                                                                                    |
| `description`     | string         | 説明メモ                                                                                                      |
| `createdAt`       | string         | ISO 8601                                                                                                      |
| `tableName`       | string         | 分析対象テーブル名                                                                                            |
| `resultType`      | string         | `regression` / `confidence_interval` / `descriptive_statistics` / `statistical_test` / `did` / `heckman` など |
| `resultTypeLabel` | string         | 分析種別の日本語ラベル                                                                                        |
| `modelType`       | string \| null | `ols` / `fe` / `re` / `iv` 等                                                                                 |
| `summaryText`     | string         | 一覧表示用の簡潔な説明文                                                                                      |

**`POST /analysis/results/output` リクエスト**

```json
{
  "resultType": "regression",
  "resultIds": ["<uuid1>", "<uuid2>"],
  "format": "markdown",
  "options": {
    "statInParentheses": "se",
    "significanceStars": null,
    "variableLabels": { "x1": "収入" },
    "constAtBottom": true,
    "variableOrder": null
  }
}
```

- `format`: `text` / `markdown` / `latex`
- `statInParentheses`: `se`（標準誤差） / `t`（t 値） / `p`（p 値） / `none`
- `significanceStars`: null = デフォルト（0.01:`***`, 0.05:`**`, 0.1:`*`）
- `resultType`: `regression` / `descriptive_statistics` / `confidence_interval` / `statistical_test`

---

### 7.7 分布プレビュー（`/distribution`）

| メソッド | パス                    | 概要                                                 |
| -------- | ----------------------- | ---------------------------------------------------- |
| POST     | `/distribution/preview` | 確率分布のパラメータからサンプル・密度を計算して返す |

**対応分布** (`DistributionType`):
`uniform` / `exponential` / `normal` / `gamma` / `beta` / `weibull` / `lognormal` / `binomial` / `bernoulli` / `poisson` / `geometric` / `hypergeometric` / `negative_binomial` / `chi_square` / `f_distribution` / `fixed` / `sequence`

---

### 7.8 モンテカルロシミュレーション（`/simulation`）

OLS の統計的性質を教育目的でシミュレーションするエンドポイント群。

| メソッド | パス                               | 概要                                                         |
| -------- | ---------------------------------- | ------------------------------------------------------------ |
| POST     | `/simulation/confidence-interval`  | 信頼区間の被覆率シミュレーション                             |
| POST     | `/simulation/asymptotic-normality` | OLS 推定量の漸近正規性シミュレーション                       |
| POST     | `/simulation/consistency`          | OLS の一致性シミュレーション（サンプルサイズ増加に伴う収束） |
| POST     | `/simulation/unbiasedness`         | OLS の不偏性シミュレーション（標本分布）                     |

**`POST /simulation/confidence-interval` リクエスト**

| パラメータ        | 制約                    | デフォルト |
| ----------------- | ----------------------- | ---------- |
| `ciType`          | `"mean"` / `"variance"` | `"mean"`   |
| `trials`          | 10〜2000                | 100        |
| `sampleSize`      | 5〜500                  | 30         |
| `confidenceLevel` | 0.90 / 0.95 / 0.99 のみ | 0.95       |
| `trueMean`        | -100〜100               | 0.0        |
| `trueVariance`    | 0.01〜100               | 1.0        |

**`POST /simulation/asymptotic-normality` リクエスト**

| パラメータ       | 制約                 | デフォルト |
| ---------------- | -------------------- | ---------- |
| `sampleSize`     | 10/20/30/50/100/1000 | 100        |
| `numSimulations` | 10〜2000             | 1000       |
| `trueBeta`       | -3〜3                | 1.0        |
| `errorVariance`  | 0.1〜10              | 1.0        |

---

### 7.9 設定（`/settings`）

| メソッド | パス        | 概要                                           |
| -------- | ----------- | ---------------------------------------------- |
| GET      | `/settings` | 現在の設定を取得                               |
| PUT      | `/settings` | 設定を部分更新（省略フィールドは現在値を維持） |

**設定フィールド**

| フィールド       | 型     | 制約                                             |
| ---------------- | ------ | ------------------------------------------------ |
| `language`       | string | `ja` または `en`                                 |
| `theme`          | string | `light` または `dark`                            |
| `encoding`       | string | ファイルエンコーディング                         |
| `logPath`        | string | ログ出力先パス                                   |
| `lastOpenedPath` | string | 最後に開いたフォルダパス（読み取り専用的に扱う） |

---

### 7.10 シャットダウン（`/shutdown`）

| メソッド | パス        | 概要                       |
| -------- | ----------- | -------------------------- |
| POST     | `/shutdown` | アプリ終了前クリーンアップ |

フロントエンドの `CloseRequested` ハンドラから呼び出す。
`AnalysisResultStore.clear_all()` + `SettingsStore` のファイル書き込みを実行。

---

## 8. エラーコード一覧

### 列操作

| コード                               | 説明                           |
| ------------------------------------ | ------------------------------ |
| `ADD_COLUMN_PROCESS_ERROR`           | 列追加処理エラー               |
| `CALCULATION_EXPRESSION_ERROR`       | 計算式エラー                   |
| `CALCULATE_COLUMN_PROCESS_ERROR`     | 計算列処理エラー               |
| `TRANSFORM_METHOD_ERROR`             | 変換種別エラー                 |
| `ADD_DUMMY_COLUMN_NULL_VALUES_FOUND` | ダミー変数追加時に Null 値検出 |
| `CAST_COLUMN_TYPE_ERROR`             | 型変換エラー                   |

### データ I/O

| コード                                          | 説明                     |
| ----------------------------------------------- | ------------------------ |
| `UNSUPPORTED_FILE_TYPE`                         | 非対応拡張子             |
| `TABLE_NOT_FOUND`                               | テーブルが存在しない     |
| `PERMISSION_DENIED`                             | ファイルアクセス権限なし |
| `CSV_IMPORT_ERROR` / `CSV_EXPORT_ERROR`         | CSV 処理エラー           |
| `EXCEL_IMPORT_ERROR` / `EXCEL_EXPORT_ERROR`     | Excel 処理エラー         |
| `PARQUET_IMPORT_ERROR` / `PARQUET_EXPORT_ERROR` | Parquet 処理エラー       |

### 回帰分析

| コード                                 | 説明                                                |
| -------------------------------------- | --------------------------------------------------- |
| `RESULT_NOT_FOUND`                     | 分析結果 ID が存在しない                            |
| `REGRESSION_PROCESS_ERROR`             | 回帰分析処理エラー                                  |
| `REGRESSION_SINGULAR_MATRIX_ERROR`     | 特異行列エラー（多重共線性）                        |
| `MISSING_VALUES_FOUND`                 | 欠損値が存在する（`missingValueHandling=error` 時） |
| `NO_VALID_OBSERVATIONS`                | 有効観測数ゼロ                                      |
| `MODEL_FILE_NOT_FOUND`                 | 診断列用モデルファイルが存在しない（一時停止中）    |
| `ADD_DIAGNOSTIC_COLUMNS_PROCESS_ERROR` | 診断列追加処理エラー                                |
| `INVALID_WEIGHTS_VALUES`               | WLS の重み列に非正値が含まれる                      |
| `SIGMA_DIMENSION_MISMATCH`             | GLS の Σ 行列次元不一致                             |
| `HECKMAN_REGRESSION_PROCESS_ERROR`     | Heckman 推定エラー                                  |
| `OUTPUT_RESULT_ERROR`                  | 結果出力エラー                                      |

### 統計分析

| コード                             | 説明                                |
| ---------------------------------- | ----------------------------------- |
| `CONFIDENCE_INTERVAL_ERROR`        | 信頼区間計算エラー                  |
| `INVALID_PROPORTION_DATA`          | 割合 CI 計算時に 0/1 以外の値を検出 |
| `DESCRIPTIVE_STATISTICS_ERROR`     | 記述統計エラー                      |
| `CORRELATION_TABLE_CREATION_ERROR` | 相関行列生成エラー                  |
| `STATISTICAL_TEST_ERROR`           | 統計的検定エラー                    |

### テーブル操作

| コード                       | 説明                                         |
| ---------------------------- | -------------------------------------------- |
| `JOIN_TABLE_CREATION_ERROR`  | 結合テーブル生成エラー                       |
| `UNION_TABLE_CREATION_ERROR` | ユニオンテーブル生成エラー（列数不一致など） |
| `COLUMN_COUNT_MISMATCH`      | ユニオン時の列数不一致                       |

### バリデーション

| コード                | 説明                                |
| --------------------- | ----------------------------------- |
| `VALIDATION_ERROR`    | Pydantic スキーマバリデーション失敗 |
| `DATA_ALREADY_EXISTS` | テーブル・列名の重複                |
| `DATA_NOT_FOUND`      | 指定した列・テーブルが存在しない    |
| `INVALID_DTYPE`       | 列の型が操作に非対応                |

---

## 9. セキュリティ要件

- **列名・テーブル名**: Pydantic の `ColumnName` / `TableName` 型で制約。Polars フィルタ式への文字列直接結合禁止
- **ファイルパス**: `FilePath` / `DirectoryPath` 型で絶対パス・存在確認済み。ユーザー入力パスをそのまま結合しない
- **分析結果 ID**: UUID 形式のみ許可（`result_id: str, Path(min_length=1)` + サービス層で UUID 検証）
- **CORS**: `tauri://localhost` のみ許可（本番）。`http://localhost:*` は開発モードフラグが必要
- **pickle 禁止**: `pickle.load` は任意コード実行可能なため使用禁止（§10 の移行を参照）

---

## 10. 未完了タスク: 診断列データ永続化（pickle 廃止 → SQLite BLOB 移行）

現在 `save_model()` は no-op で、`add-diagnostic-columns` は `MODEL_FILE_NOT_FOUND` を返す一時停止状態。

### 背景

`pickle.load` は任意コード実行可能なフォーマットのためセキュリティリスクあり。
`numpy.savez_compressed` + SQLite BLOB に移行することで安全に永続化する。

### 保存データ構造 `DiagnosticArrays`

| フィールド     | 型                   | 内容                                 |
| -------------- | -------------------- | ------------------------------------ |
| `fittedvalues` | `np.ndarray`         | 予測値                               |
| `resid`        | `np.ndarray \| None` | 残差                                 |
| `resid_std`    | `np.ndarray \| None` | 標準化残差（OLS のみ）               |
| `ci_lower_95`  | `np.ndarray \| None` | 予測値 95% CI 下限（OLS のみ）       |
| `ci_upper_95`  | `np.ndarray \| None` | 予測値 95% CI 上限（OLS のみ）       |
| `row_indices`  | `np.ndarray`         | 0-based 行インデックス（欠損除去後） |

### SQLite スキーマ

```sql
CREATE TABLE IF NOT EXISTS diagnostic_arrays (
    result_id  TEXT PRIMARY KEY,  -- UUID
    data       BLOB NOT NULL,     -- numpy.savez_compressed の BytesIO
    created_at TEXT NOT NULL
);
```

DB ファイルパス: `get_tmp_models_dir()` 配下の `diagnostic_arrays.db`
読み込み時は必ず `numpy.load(allow_pickle=False)` を使用すること。

### 変更対象ファイル

| ファイル                                                         | 変更内容                                                     |
| ---------------------------------------------------------------- | ------------------------------------------------------------ |
| `api/economicon/services/data/analysis_result.py`                | `save_model` / `load_model` → 診断配列 I/O に置き換え        |
| `api/economicon/services/data/analysis_result_store.py`          | `save_diagnostic_arrays()` / `load_diagnostic_arrays()` 追加 |
| `api/economicon/services/regressions/estimators/_base.py`        | 推定後に診断配列を保存                                       |
| `api/economicon/services/selection_models/heckman_regression.py` | 同上（step1/step2 両段階）                                   |
| `api/economicon/services/regressions/add_diagnostic_columns.py`  | `load_model()` → `load_diagnostic_arrays()` に切り替え       |

### テスト再有効化条件

`api/tests/regressions/test_add_diagnostic_columns.py` および
`api/tests/selection_models/heckman/test_heckman.py` の `@pytest.mark.skip` を外す。

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

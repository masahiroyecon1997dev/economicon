# DID（差の差）分析 API 仕様書

**バージョン**: 0.4.0
**最終更新**: 2026-04-18
**エンドポイント**: `POST /analysis/did`

---

## 概要

Two-Way Fixed Effects（TWFE）に基づく差の差（Difference-in-Differences; DID）推定を実行する。
交差項 `treated_i × post_t` をサービス層で自動生成し、個体固定効果・時点固定効果を除去した上で ATT（Average Treatment Effect on the Treated）を推定する。
オプションで Event Study（各時点の処置効果推定）も実行可能。

### 推定式

**基本 DID（TWFE）**

$$y_{it} = \alpha + \beta \cdot (D_i \times P_t) + \sum_k \gamma_k X_{kit} + \mu_i + \tau_t + \varepsilon_{it}$$

- $D_i$: 処置群ダミー（`treatmentColumn`）
- $P_t$: 処置後ダミー（`postColumn`）
- $\mu_i$: 個体固定効果
- $\tau_t$: 時点固定効果
- $\beta$: **DID 推定量（ATT）**

**Event Study**

$$y_{it} = \alpha + \sum_{k \neq k_{\text{base}}} \delta_k \cdot (D_i \times \mathbf{1}[t = k]) + \sum_j \gamma_j X_{jit} + \mu_i + \tau_t + \varepsilon_{it}$$

- $\delta_k$: 相対期間 $k$ における処置効果（`basePeriod` の係数は 0 に固定）

---

## エンドポイント設計

### エンドポイントを `/analysis/regression` と分離する理由

| 観点           | 理由                                                                                                                                |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| スキーマ構造   | `treatmentColumn` / `postColumn` / `entityIdColumn` / `timeColumn` / `includeEventStudy` など、回帰とは完全に異なるパラメータセット |
| 自動処理       | 交差項（`treated × post`）の自動生成・Event Study 用相互作用項の自動生成                                                            |
| 出力構造       | `didEstimate`（ATT）/ `eventStudy`（期間別係数）など DID 固有フィールドを持つ                                                       |
| 推定ライブラリ | `linearmodels.PanelOLS`（TWFE）を主軸に使用（`statsmodels.OLS` とは異なる API）                                                     |

---

## ライブラリ選定

| 手法               | ライブラリ                          | 備考                                                      |
| ------------------ | ----------------------------------- | --------------------------------------------------------- |
| 基本 DID（TWFE）   | `linearmodels.PanelOLS`             | `entity_effects=True, time_effects=True` で自然に指定可能 |
| Event Study        | `linearmodels.PanelOLS`             | 相互作用項を Polars で生成後に同一 API で推定             |
| クラスタ標準誤差   | `linearmodels`                      | `cov_type='clustered', cluster_entity=True`               |
| 並行トレンド検定   | `linearmodels.PanelOLS.wald_test()` | 処置前係数の Wald/F 検定                                  |
| 補助（FEなし OLS） | `statsmodels.OLS`                   | 必要に応じて比較用途のみ                                  |

---

## リクエスト仕様

### エンドポイント

```
POST /analysis/did
```

### リクエストボディ（JSON）

```json
{
  "tableName": "policy_data",
  "resultName": "",
  "description": "",
  "dependentVariable": "employment",
  "explanatoryVariables": ["age", "education"],
  "treatmentColumn": "treated",
  "postColumn": "post",
  "timeColumn": "year",
  "entityIdColumn": "firm_id",
  "includeEventStudy": true,
  "basePeriod": -1,
  "maxPrePeriods": null,
  "maxPostPeriods": null,
  "missingValueHandling": "remove",
  "standardError": {
    "method": "cluster",
    "groups": ["firm_id"],
    "useCorrection": true
  },
  "confidenceLevel": 0.95
}
```

### パラメータ詳細

| フィールド（camelCase） | 型              | 必須 | デフォルト | 説明                                     |
| ----------------------- | --------------- | ---- | ---------- | ---------------------------------------- |
| `tableName`             | string          | ✅   | —          | 分析対象テーブル名                       |
| `resultName`            | string          | —    | `""`       | 結果の表示名（空の場合は自動生成）       |
| `description`           | string          | —    | `""`       | 説明メモ（最大 512 文字）                |
| `dependentVariable`     | string          | ✅   | —          | 被説明変数列名（数値型）                 |
| `explanatoryVariables`  | string[]        | —    | `[]`       | 追加共変量列名リスト（空可）             |
| `treatmentColumn`       | string          | ✅   | —          | 処置群ダミー列名（0/1, 数値型）          |
| `postColumn`            | string          | ✅   | —          | 処置後ダミー列名（0/1, 数値型）          |
| `timeColumn`            | string          | ✅   | —          | 時点列名（数値型または Date 型）         |
| `entityIdColumn`        | string          | ✅   | —          | 個体 ID 列名                             |
| `includeEventStudy`     | boolean         | —    | `false`    | Event Study を実行するか                 |
| `basePeriod`            | integer \| null | —    | `null`     | Event Study 基準期（null=自動選択）      |
| `maxPrePeriods`         | integer \| null | —    | `null`     | Event Study 処置前期間数の上限           |
| `maxPostPeriods`        | integer \| null | —    | `null`     | Event Study 処置後期間数の上限           |
| `missingValueHandling`  | enum            | —    | `"remove"` | `remove` / `ignore` / `error`            |
| `standardError`         | object          | ✅   | —          | 標準誤差設定（後述）。**`cluster` 推奨** |
| `confidenceLevel`       | float           | —    | `0.95`     | 信頼区間水準（0.5 〜 0.999）             |

#### `standardError` の例（クラスタ SE を推奨）

```json
{ "method": "cluster", "groups": ["firm_id"], "useCorrection": true }
```

> **DID における標準誤差の選択指針**
> 処置の割り当ては通常個体レベルで行われるため、個体内の誤差が系列相関を持つ。
> クラスタ標準誤差（個体レベル）を使用することで、この系列相関に頑健な推定が可能。
> `nonrobust` や `robust` はパネル系列相関を考慮しないため非推奨。

---

## バリデーション仕様

### validate() で確認する項目

| チェック内容     | エラーコード       | 説明                                                                                                          |
| ---------------- | ------------------ | ------------------------------------------------------------------------------------------------------------- |
| テーブル存在確認 | `VALIDATION_ERROR` | `tableName` がワークスペースに存在すること                                                                    |
| 列存在確認       | `VALIDATION_ERROR` | 全指定列がテーブルに存在すること                                                                              |
| 数値型確認       | `VALIDATION_ERROR` | `dependentVariable` / `treatmentColumn` / `postColumn` / `explanatoryVariables` が数値型であること            |
| 重複列禁止       | `DUPLICATE_COLUMN` | `explanatoryVariables` が `treatmentColumn` / `postColumn` / `entityIdColumn` / `timeColumn` と重複しないこと |

### execute() で確認する項目

| チェック内容            | エラーコード               | タイミング                                                           |
| ----------------------- | -------------------------- | -------------------------------------------------------------------- |
| `basePeriod` の存在確認 | `VALIDATION_ERROR`         | データ読み込み後、`basePeriod` が実データの時点集合に含まれること    |
| 個体×時点のユニーク性   | `VALIDATION_ERROR`         | 同一個体・同一時点の重複行が存在しないこと（非バランスパネルは許容） |
| 有効観測数確認          | `NO_VALID_OBSERVATIONS`    | 欠損値除去後に観測数がゼロにならないこと                             |
| 収束失敗                | `REGRESSION_PROCESS_ERROR` | `linearmodels` が推定失敗した場合                                    |

---

## レスポンス仕様

### 成功レスポンス

```json
{
  "code": "OK",
  "result": {
    "resultId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

分析結果の詳細は `GET /analysis/results/{resultId}` で取得する。

---

## result_data 構造（GET /analysis/results/{id} の `resultData` フィールド）

```json
{
  "tableName": "policy_data",
  "dependentVariable": "employment",
  "treatmentColumn": "treated",
  "postColumn": "post",
  "timeColumn": "year",
  "entityIdColumn": "firm_id",
  "confidenceLevel": 0.95,
  "didEstimate": {
    "coefficient": 0.152,
    "standardError": 0.043,
    "tValue": 3.53,
    "pValue": 0.0004,
    "ciLower": 0.068,
    "ciUpper": 0.236,
    "description": "ATT: Average Treatment Effect on the Treated (TWFE)"
  },
  "parameters": [
    {
      "name": "age",
      "coefficient": 0.012,
      "standardError": 0.005,
      "tValue": 2.4,
      "pValue": 0.016,
      "ciLower": 0.002,
      "ciUpper": 0.022
    }
  ],
  "modelStatistics": {
    "nObservations": 800,
    "nTreated": 400,
    "nControl": 400,
    "nPeriods": 4,
    "r2": 0.38,
    "adjustedR2": 0.37,
    "fValue": 42.1,
    "fProbability": 0.0001
  },
  "diagnostics": {
    "preTrendTest": {
      "fStatistic": 0.82,
      "df1": 2,
      "df2": 380,
      "pValue": 0.413,
      "description": "Test for parallel trends assumption (Wald test on pre-period coefficients). Non-significant p-value supports parallel trends."
    }
  },
  "eventStudy": [
    {
      "period": -2,
      "coefficient": -0.01,
      "standardError": 0.03,
      "tValue": -0.33,
      "pValue": 0.74,
      "ciLower": -0.07,
      "ciUpper": 0.05
    },
    {
      "period": -1,
      "coefficient": 0.0,
      "standardError": 0.0,
      "tValue": 0.0,
      "pValue": 1.0,
      "ciLower": 0.0,
      "ciUpper": 0.0
    },
    {
      "period": 0,
      "coefficient": 0.15,
      "standardError": 0.04,
      "tValue": 3.75,
      "pValue": 0.0,
      "ciLower": 0.07,
      "ciUpper": 0.23
    },
    {
      "period": 1,
      "coefficient": 0.18,
      "standardError": 0.04,
      "tValue": 4.5,
      "pValue": 0.0,
      "ciLower": 0.1,
      "ciUpper": 0.26
    }
  ]
}
```

### result_data フィールド定義

#### `didEstimate`（ATT）

| フィールド      | 型     | 説明                     |
| --------------- | ------ | ------------------------ |
| `coefficient`   | float  | DID 推定量（交差項係数） |
| `standardError` | float  | 標準誤差                 |
| `tValue`        | float  | t 統計量                 |
| `pValue`        | float  | p 値                     |
| `ciLower`       | float  | 信頼区間下限             |
| `ciUpper`       | float  | 信頼区間上限             |
| `description`   | string | 推定量の説明文           |

#### `modelStatistics`

| フィールド      | 型    | 説明                   |
| --------------- | ----- | ---------------------- |
| `nObservations` | int   | 総観測数（個体×時点）  |
| `nTreated`      | int   | 処置群のユニーク個体数 |
| `nControl`      | int   | 対照群のユニーク個体数 |
| `nPeriods`      | int   | ユニーク時点数         |
| `r2`            | float | 決定係数 R²            |
| `adjustedR2`    | float | 自由度修正済み R²      |
| `fValue`        | float | F 統計量               |
| `fProbability`  | float | F 検定の p 値          |

#### `diagnostics.preTrendTest`

並行トレンド仮定の検定（Event Study 実行時のみ非 null）。

帰無仮説 $H_0: \delta_k = 0 \quad \forall k < 0, k \neq k_{\text{base}}$

| フィールド    | 型     | 説明                                         |
| ------------- | ------ | -------------------------------------------- |
| `fStatistic`  | float  | F 統計量（Wald 検定）                        |
| `df1`         | int    | 分子の自由度（処置前期間数 - 1）             |
| `df2`         | int    | 分母の自由度                                 |
| `pValue`      | float  | p 値。非有意（p > 0.05）が並行トレンドを支持 |
| `description` | string | 解釈文                                       |

#### `eventStudy`（各要素）

| フィールド      | 型    | 説明                                   |
| --------------- | ----- | -------------------------------------- |
| `period`        | int   | 処置からの相対期間                     |
| `coefficient`   | float | 係数推定値 $\delta_k$                  |
| `standardError` | float | 標準誤差                               |
| `tValue`        | float | t 統計量                               |
| `pValue`        | float | p 値                                   |
| `ciLower`       | float | 信頼区間下限（Event Study プロット用） |
| `ciUpper`       | float | 信頼区間上限（Event Study プロット用） |

> `basePeriod` の行は `coefficient=0.0`, `standardError=0.0` として含める（基準点の明示）。

---

## 実装時の注意事項

### linearmodels との Pandas 連携

```python
# Polars → MultiIndex Pandas DataFrame への変換（linearmodels 必須）
# entity_id を第1レベル、time を第2レベルとする
df_pd = (
    df_pl.to_pandas()
       .set_index([entity_id_column, time_column])
       .sort_index()
)

# TWFE 推定
from linearmodels.panel import PanelOLS
model = PanelOLS(
    dependent=df_pd[dependent_variable],
    exog=df_pd[regressors],  # 交差項を含む
    entity_effects=True,
    time_effects=True,
)
result = model.fit(cov_type='clustered', cluster_entity=True)
```

### Event Study 用交差項の生成（Polars）

```python
# time_column の各ユニーク値を列挙し、base_period を除いて交差項を生成
import polars as pl

periods = sorted(df.get_column(time_column).unique().to_list())
base = base_period  # 例: -1

for p in periods:
    if p == base:
        continue
    col_name = f"es_{p}"
    df = df.with_columns(
        (pl.col(treatment_column) * (pl.col(time_column) == p).cast(pl.Int8))
        .alias(col_name)
    )
```

### 並行トレンド検定（Wald 検定）

```python
# pre_period 係数名リスト（base_period を除く）
pre_cols = [f"es_{p}" for p in periods if p < 0 and p != base]
# linearmodels の Wald 検定
wald = result.wald_test(formula=", ".join(pre_cols))
# wald.stat: F 統計量, wald.pval: p 値
# df1 = len(pre_cols), df2 = result.df_resid
```

---

## エラーレスポンス

| HTTP | エラーコード               | 発生条件                                         |
| ---- | -------------------------- | ------------------------------------------------ |
| 400  | `VALIDATION_ERROR`         | 列が存在しない / 数値型でない / パラメータ範囲外 |
| 400  | `DUPLICATE_COLUMN`         | `explanatoryVariables` に予約列が含まれる        |
| 422  | `VALIDATION_ERROR`         | リクエストボディの型・形式エラー                 |
| 501  | `NOT_IMPLEMENTED`          | ビジネスロジック未実装（現在）                   |
| 500  | `REGRESSION_PROCESS_ERROR` | 推定失敗・収束失敗                               |

---

## 未決事項・TODO

- [ ] Event Study の `maxPrePeriods` / `maxPostPeriods` による期間フィルタリングの実装
- [ ] フロントエンド: Event Study プロット用コンポーネントの設計
- [ ] `result_type` 文字列を `"did"` として既存の結果管理 UI に組み込む

### 多時点処置（Staggered Adoption）を実装しない理由

Callaway & Sant'Anna (2021) や Sun & Abraham (2021) 等の手法は、
成熟した Python パッケージが存在しないため手動実装が必要となる。
推定結果の正確性を R の参照実装（`fixest::sunab`、`did::att_gt`）と
照合するコストが高く、テストによる正確性担保が現実的でない。
また推定量の選択自体が現在もアクティブな研究領域であり、
実装判断のコンセンサスが確立されていないため、現バージョンでは対象外とする。

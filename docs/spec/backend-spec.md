# Backend Spec

## 目的

バックエンド API の設計仕様と未解消の実装課題を管理する。

## 運用ルール

- 未実装・未修正の項目だけを記載する。
- 実装完了を確認した項目はこの文書から削除する。
- フロントエンドに影響する API 変更は `docs/spec/frontend-spec.md` と合わせて管理する。

---

## 統計ビジュアライゼーション シミュレーション API

`docs/spec/frontend-spec.md` の「Plotly.js を使った統計ビジュアライゼーション」に対応する新規 API。

### 実装対象ファイル（新規）

| ファイル                                                        | 役割                              |
| --------------------------------------------------------------- | --------------------------------- |
| `api/economicon/routers/simulation.py`                          | ルーター（prefix: `/simulation`） |
| `api/economicon/schemas/simulation.py`                          | リクエスト・レスポンス スキーマ   |
| `api/economicon/services/simulation/confidence_interval_sim.py` | 信頼区間シミュレーション          |
| `api/economicon/services/simulation/asymptotic_normality.py`    | 漸近正規性シミュレーション        |
| `api/economicon/services/simulation/consistency.py`             | 一致性シミュレーション            |
| `api/economicon/services/simulation/unbiasedness.py`            | 不偏性シミュレーション            |

### 共通仕様

- テーブルストア（`TablesStore`）に**依存しない**（純粋なシミュレーション）
- 乱数シードはユーザー指定不可（毎回ランダム）
- 回帰モデル: `y_i = α + β·x_i + ε_i`（切片あり単回帰。表示するのは傾き β のみ）
- 説明変数 x: `N(x_mean, x_variance)` からサンプリング
- 全結果を一括返却。アニメーションはフロントエンドが担当

### 共通スキーマ

#### `XDistributionParams`（ネストオブジェクト、回帰系3エンドポイントで共用）

| フィールド   | 型      | 制約          | デフォルト | 説明                |
| ------------ | ------- | ------------- | ---------- | ------------------- |
| `x_mean`     | `float` | -10.0 〜 10.0 | 0.0        | 説明変数 x の母平均 |
| `x_variance` | `float` | 0.1 〜 10.0   | 1.0        | 説明変数 x の母分散 |

---

### エンドポイント 1: `POST /simulation/confidence-interval`

**概要**: M 回のサンプリングを行い各試行の信頼区間を計算する。被覆確率の定義を視覚的に示す。

#### リクエスト `ConfidenceIntervalSimRequestBody`

| フィールド         | 型                       | 制約                        | デフォルト | 説明                                             |
| ------------------ | ------------------------ | --------------------------- | ---------- | ------------------------------------------------ |
| `ci_type`          | `"mean"` \| `"variance"` | -                           | 必須       | 信頼区間の種類                                   |
| `trials`           | `int`                    | 10 〜 2000                  | 100        | 試行回数 M                                       |
| `sample_size`      | `int`                    | 5 〜 500                    | 30         | 各試行のサンプルサイズ n                         |
| `confidence_level` | `float`                  | 0.90, 0.95, 0.99 のいずれか | 0.95       | 信頼水準                                         |
| `true_mean`        | `float`                  | -100.0 〜 100.0             | 0.0        | 真の母平均 μ（`ci_type="mean"` 時のみ使用）      |
| `true_variance`    | `float`                  | 0.01 〜 100.0               | 1.0        | 真の母分散 σ²（`ci_type="variance"` 時のみ使用） |

#### レスポンス `SuccessResponse[ConfidenceIntervalSimResult]`

| フィールド         | 型              | 説明                                                   |
| ------------------ | --------------- | ------------------------------------------------------ |
| `true_value`       | `float`         | グラフの垂直線用の真の値（`ci_type` に応じて μ or σ²） |
| `confidence_level` | `float`         | リクエストの信頼水準（echo）                           |
| `intervals`        | `list[CIBound]` | M 件の信頼区間（順番 = 試行番号 1〜M）                 |

`CIBound`:

| フィールド      | 型      | 説明           |
| --------------- | ------- | -------------- |
| `lower`         | `float` | 信頼区間の下限 |
| `upper`         | `float` | 信頼区間の上限 |
| `contains_true` | `bool`  | 真の値を含むか |

#### 計算仕様

- `ci_type="mean"`: N(true*mean, true_variance) からサンプリング。t 分布を用いた区間推定 `(x̄ ± t*{α/2} · s/√n)`
- `ci_type="variance"`: N(true*mean, true_variance) からサンプリング。χ² 分布を用いた区間推定 `((n-1)s²/χ²*{α/2}, (n-1)s²/χ²\_{1-α/2})`

---

### エンドポイント 2: `POST /simulation/asymptotic-normality`

**概要**: 同一パラメータで num_simulations 回 OLS を行い β̂ の標本分布を返す。n の選択と誤差分布スイッチで漸近正規性の成立・不成立を比較できる。

#### リクエスト `AsymptoticNormalityRequestBody`

| フィールド             | 型                                         | 制約        | デフォルト                   | 説明                                                   |
| ---------------------- | ------------------------------------------ | ----------- | ---------------------------- | ------------------------------------------------------ |
| `sample_size`          | `Literal[10, 20, 30, 50, 100, 1000]`       | -           | 100                          | サンプルサイズ n                                       |
| `num_simulations`      | `int`                                      | 10 〜 2000  | 1000                         | シミュレーション回数                                   |
| `true_beta`            | `float`                                    | -3.0 〜 3.0 | 1.0                          | 真の回帰係数 β                                         |
| `error_variance`       | `float`                                    | 0.1 〜 10.0 | 1.0                          | 誤差項の分散 σ²（`error_type="normal"` 時のみ使用）    |
| `error_type`           | `"normal"` \| `"cauchy"` \| `"endogenous"` | -           | `"normal"`                   | 誤差分布の種類                                         |
| `endogeneity_strength` | `float`                                    | 0.1 〜 3.0  | 1.0                          | 内生性の強さ γ（`error_type="endogenous"` 時のみ使用） |
| `x_distribution`       | `XDistributionParams`                      | -           | `{x_mean: 0, x_variance: 1}` | 説明変数 x の分布                                      |

#### レスポンス `SuccessResponse[AsymptoticNormalityResult]`

| フィールド                 | 型              | 説明                                                           |
| -------------------------- | --------------- | -------------------------------------------------------------- |
| `beta_estimates`           | `list[float]`   | num_simulations 個の β̂                                         |
| `true_beta`                | `float`         | 真の値 β                                                       |
| `is_asymptotically_normal` | `bool`          | CLT が成立するか（コーシー誤差のとき `false`）                 |
| `asymptotic_mean`          | `float \| None` | 漸近分布の平均（`is_asymptotically_normal=false` なら `None`） |
| `asymptotic_variance`      | `float \| None` | 漸近分布の分散（`is_asymptotically_normal=false` なら `None`） |

#### 計算仕様

| `error_type`   | 生成式                                                         | `is_asymptotically_normal` | `asymptotic_mean` | `asymptotic_variance` |
| -------------- | -------------------------------------------------------------- | -------------------------- | ----------------- | --------------------- |
| `"normal"`     | ε_i ~ N(0, σ²)                                                 | `true`                     | `true_beta`       | σ² / (n · Var(x))     |
| `"cauchy"`     | ε_i ~ Cauchy(0, 1)                                             | `false`                    | `None`            | `None`                |
| `"endogenous"` | z_i ~ N(0,1)、x_i = z_i + v_i、ε_i = γ·z_i + η_i (η_i~N(0,σ²)) | `true`                     | `true_beta + γ/2` | (γ²+σ²) / (2n)        |

内生性モデルの詳細: z_i ~ N(0,1)、v_i ~ N(0,1)（x と独立）、η_i ~ N(0, σ²)（v, z と独立）。γ = `endogeneity_strength`。OLS の確率極限は `β + γ·Cov(x,z)/Var(x) = β + γ/2`。

---

### エンドポイント 3: `POST /simulation/consistency`

**概要**: 1 つのデータ生成過程から n=2〜n_max まで累積的に OLS を行い、サンプルサイズ増加に伴う推定値の収束軌跡を返す。

#### リクエスト `ConsistencyRequestBody`

| フィールド             | 型                    | 制約        | デフォルト                   | 説明                                           |
| ---------------------- | --------------------- | ----------- | ---------------------------- | ---------------------------------------------- |
| `n_max`                | `int`                 | 50 〜 5000  | 500                          | 最大サンプルサイズ                             |
| `true_beta`            | `float`               | -3.0 〜 3.0 | 1.0                          | 真の回帰係数 β                                 |
| `error_variance`       | `float`               | 0.1 〜 10.0 | 1.0                          | 誤差項の分散 σ²                                |
| `endogenous`           | `bool`                | -           | `false`                      | 内生性ありかどうか（省略変数モデル）           |
| `endogeneity_strength` | `float`               | 0.1 〜 3.0  | 1.0                          | 内生性の強さ γ（`endogenous=true` 時のみ使用） |
| `x_distribution`       | `XDistributionParams` | -           | `{x_mean: 0, x_variance: 1}` | 説明変数 x の分布                              |

#### レスポンス `SuccessResponse[ConsistencyResult]`

| フィールド          | 型            | 説明                                                                             |
| ------------------- | ------------- | -------------------------------------------------------------------------------- |
| `n_values`          | `list[int]`   | サンプルサイズの系列（2, 3, ..., n_max）                                         |
| `beta_estimates`    | `list[float]` | 各 n での OLS 推定値 β̂                                                           |
| `true_beta`         | `float`       | 真の値 β（グラフの水平破線）                                                     |
| `probability_limit` | `float`       | 推定量の確率極限（外生性成立なら `true_beta`、内生性ありなら `true_beta + γ/2`） |

#### 計算仕様

- n_max のデータを 1 回生成し、n=2, 3, ..., n_max の各サイズで OLS を実行（累積推定）
- `endogenous=true` の場合: z_i ~ N(0,1)、x_i = z_i + v_i (v_i~N(0,1))、y_i = α + β·x_i + γ·z_i + η_i (η_i~N(0,σ²))、γ = `endogeneity_strength`

---

### エンドポイント 4: `POST /simulation/unbiasedness`

**概要**: 同一母集団から M 回独立にサンプリングして OLS を行い β̂ の標本分布を返す。β̂ の平均が真の値 β に収束することを示す。

#### リクエスト `UnbiasednessRequestBody`

| フィールド       | 型                    | 制約        | デフォルト                   | 説明                     |
| ---------------- | --------------------- | ----------- | ---------------------------- | ------------------------ |
| `num_trials`     | `int`                 | 10 〜 2000  | 200                          | 試行回数 M               |
| `sample_size`    | `int`                 | 5 〜 500    | 50                           | 各試行のサンプルサイズ n |
| `true_beta`      | `float`               | -3.0 〜 3.0 | 1.0                          | 真の回帰係数 β           |
| `error_variance` | `float`               | 0.1 〜 10.0 | 1.0                          | 誤差項の分散 σ²          |
| `x_distribution` | `XDistributionParams` | -           | `{x_mean: 0, x_variance: 1}` | 説明変数 x の分布        |

#### レスポンス `SuccessResponse[UnbiasednessResult]`

| フィールド       | 型            | 説明                                |
| ---------------- | ------------- | ----------------------------------- |
| `beta_estimates` | `list[float]` | num_trials 個の β̂（各試行の推定値） |
| `true_beta`      | `float`       | 真の値 β                            |

> **フロントエンド側での計算**: 累積平均 = `mean(beta_estimates[0:k])` for k=1,...,M。第2プロットの縦軸 = 累積平均 − `true_beta`。

---

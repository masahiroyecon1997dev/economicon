# Backend Spec

## 目的

バックエンド API の設計仕様と未解消の実装課題を管理する。

## 運用ルール

- 未実装・未修正の項目だけを記載する。
- 実装完了を確認した項目はこの文書から削除する。
- フロントエンドに影響する API 変更は `docs/spec/frontend-spec.md` と合わせて管理する。

---

## 実装計画: 分布プレビュー API

### エンドポイント

`POST /api/distribution/preview`

### リクエストスキーマ: `DistributionPreviewRequestBody`

```json
{
  "distribution": { "type": "normal", "mean": 0.0, "standard_deviation": 1.0 },
  "x_count": 200
}
```

| フィールド     | 型                   | バリデーション                          | デフォルト | 説明                                                     |
| -------------- | -------------------- | --------------------------------------- | ---------: | -------------------------------------------------------- |
| `distribution` | `DistributionConfig` | FIXED / SEQUENCE は `validate()` で拒否 |          — | 既存スキーマを流用。chi_square / f_distribution も対象。 |
| `x_count`      | `int`                | `ge=50, le=2000`                        |        200 | 連続分布のグラフ点数。離散分布は整数範囲が点数になる。   |

### レスポンススキーマ: `DistributionPreviewResult`

```json
{
  "is_discrete": false,
  "x": [
    /* float のリスト */
  ],
  "y_density": [
    /* PDF または PMF 値 */
  ],
  "y_cumulative": [
    /* CDF または CMF 値 */
  ]
}
```

| フィールド     | 型            | 説明                                    |
| -------------- | ------------- | --------------------------------------- |
| `is_discrete`  | `bool`        | 離散分布のとき `true`                   |
| `x`            | `list[float]` | X 軸の値のリスト（離散も float で返す） |
| `y_density`    | `list[float]` | PDF（連続）または PMF（離散）の値       |
| `y_cumulative` | `list[float]` | CDF（連続）または CMF（離散）の値       |

### X 軸範囲の計算ロジック（`scipy.stats` を使用）

連続分布は `x_count` 点の等間隔グリッド。離散分布は PMF > 1e-6 となる整数範囲で点数は
範囲の広さに依存し `x_count` は上限として使用する。

| 分布              | `scipy.stats` クラス                        | X 下限                  | X 上限       | 備考                                     |
| ----------------- | ------------------------------------------- | ----------------------- | ------------ | ---------------------------------------- |
| uniform           | `uniform(loc=low, scale=high-low)`          | `low`                   | `high`       | パラメータから直接算出                   |
| exponential       | `expon(scale=scale)`                        | 0                       | `ppf(0.995)` |                                          |
| normal            | `norm(loc=mean, scale=std)`                 | `ppf(0.005)`            | `ppf(0.995)` |                                          |
| gamma             | `gamma(a=shape, scale=scale)`               | `ppf(0.005)`            | `ppf(0.995)` |                                          |
| beta              | `beta(a=alpha, b=beta)`                     | `ppf(0.005)`            | `ppf(0.995)` |                                          |
| weibull           | `weibull_min(c=shape, scale=scale)`         | 0                       | `ppf(0.995)` | numpy の `rng.weibull(k) * scale` と等価 |
| lognormal         | `lognorm(s=log_std, scale=exp(log_mean))`   | `ppf(0.005)`            | `ppf(0.995)` |                                          |
| chi_square        | `chi2(df=degrees_of_freedom)`               | `max(ppf(0.005), 1e-4)` | `ppf(0.995)` | df ≤ 2 で下限が 0 に近くなるため保護     |
| f_distribution    | `f(dfn=numerator_df, dfd=denominator_df)`   | `max(ppf(0.005), 1e-4)` | `ppf(0.995)` | 同上                                     |
| binomial          | `binom(n=trial_count, p=prob)`              | `max(0, ppf(0.005))`    | `ppf(0.995)` | 整数点のみ                               |
| bernoulli         | `bernoulli(p=prob)`                         | 0                       | 1            | x ∈ {0, 1} 固定                          |
| poisson           | `poisson(mu=rate)`                          | 0                       | `ppf(0.995)` | 整数点のみ                               |
| geometric         | `geom(p=prob)`                              | 1                       | `ppf(0.995)` | scipy は x ≥ 1 の定義                    |
| hypergeometric    | `hypergeom(M=population, n=succ, N=sample)` | `max(0, ppf(0.005))`    | `ppf(0.995)` | 整数点のみ                               |
| negative_binomial | `nbinom(n=target, p=prob)`                  | 0                       | `ppf(0.995)` | 整数点のみ                               |

> `ppf(q)` は各分布の分位点関数（逆 CDF）。

### エラーコード

| 条件                                    | エラーコード（新規追加）                | HTTP |
| --------------------------------------- | --------------------------------------- | ---: |
| FIXED / SEQUENCE が指定された           | `DISTRIBUTION_PREVIEW_UNSUPPORTED_TYPE` |  422 |
| scipy 計算中の数値エラー（overflow 等） | `DISTRIBUTION_PREVIEW_COMPUTE_ERROR`    |  422 |

### 新規ファイル / 変更ファイル

| ファイル                                                   | 種別 | 内容                                                                    |
| ---------------------------------------------------------- | ---- | ----------------------------------------------------------------------- |
| `economicon/schemas/distribution_preview.py`               | 新規 | `DistributionPreviewRequestBody` / `DistributionPreviewResult`          |
| `economicon/services/distribution/distribution_preview.py` | 新規 | `DistributionPreview` サービス（`scipy.stats` 計算）                    |
| `economicon/routers/distribution.py`                       | 新規 | `POST /api/distribution/preview` ルーター                               |
| `economicon/schemas/enums.py`                              | 変更 | `CHI_SQUARE = "chi_square"`, `F_DISTRIBUTION = "f_distribution"` を追加 |
| `economicon/schemas/distribution_params.py`                | 変更 | 新スキーマ追加 + 全分布に `le` 制約追加（後述）                         |
| `economicon/schemas/types.py`                              | 変更 | `DistributionConfig` Union に `chi_square` / `f_distribution` を追加    |
| `economicon/utils/algorithms/simulation.py`                | 変更 | chi_square / f_distribution ジェネレータを追加                          |

---

## 実装計画: χ²・F 分布の追加（既存 API 拡張）

既存の `CreateSimulationDataTable` / `AddSimulationColumn` API にも同時に追加する。

### 追加スキーマ（`distribution_params.py`）

```python
class ChiSquareParams(BaseRequest):
    """カイ二乗分布のパラメータ"""
    type: Literal[DistributionType.CHI_SQUARE] = Field(description="分布の種類")
    degrees_of_freedom: int = Field(gt=0, le=1000, description="自由度")

class FDistributionParams(BaseRequest):
    """F 分布のパラメータ"""
    type: Literal[DistributionType.F_DISTRIBUTION] = Field(description="分布の種類")
    numerator_df: int = Field(gt=0, le=1000, description="分子自由度")
    denominator_df: int = Field(gt=0, le=1000, description="分母自由度")
```

### simulation.py への追加

```python
DistributionType.CHI_SQUARE: lambda d: rng.chisquare(
    d.degrees_of_freedom, row_count
),
DistributionType.F_DISTRIBUTION: lambda d: rng.f(
    d.numerator_df, d.denominator_df, row_count
),
```

### UI 分類（フロントエンド側への通知）

χ² 分布・F 分布はともに**連続分布タブ**に追加する（gamma / weibull 等と同列）。

---

## 実装計画: 既存 API パラメータ上限制約の追加

**スコープ**: `CreateSimulationDataTable` / `AddSimulationColumn` / `DistributionPreview` すべてに適用。

### `distribution_params.py` 変更一覧

| クラス                   | フィールド               | 変更前  | 変更後              |
| ------------------------ | ------------------------ | ------- | ------------------- |
| `UniformParams`          | `low`                    | `float` | `ge=-1000, le=1000` |
| `UniformParams`          | `high`                   | `float` | `ge=-1000, le=1000` |
| `ExponentialParams`      | `scale_parameter`        | `gt=0`  | `gt=0, le=1000`     |
| `NormalParams`           | `mean`                   | `float` | `ge=-1000, le=1000` |
| `NormalParams`           | `standard_deviation`     | `gt=0`  | `gt=0, le=500`      |
| `GammaParams`            | `shape_parameter`        | `gt=0`  | `gt=0, le=1000`     |
| `GammaParams`            | `scale_parameter`        | `gt=0`  | `gt=0, le=1000`     |
| `BetaParams`             | `alpha`                  | `gt=0`  | `gt=0, le=1000`     |
| `BetaParams`             | `beta`                   | `gt=0`  | `gt=0, le=1000`     |
| `WeibullParams`          | `shape_parameter`        | `gt=0`  | `gt=0, le=1000`     |
| `WeibullParams`          | `scale_parameter`        | `gt=0`  | `gt=0, le=1000`     |
| `LognormalParams`        | `log_mean`               | `float` | `ge=-100, le=100`   |
| `LognormalParams`        | `log_standard_deviation` | `gt=0`  | `gt=0, le=100`      |
| `BinomialParams`         | `trial_count`            | `gt=0`  | `gt=0, le=10000`    |
| `PoissonParams`          | `rate`                   | `gt=0`  | `gt=0, le=10000`    |
| `HypergeometricParams`   | `population_size`        | `gt=0`  | `gt=0, le=100000`   |
| `NegativeBinomialParams` | `target_success_count`   | `gt=0`  | `gt=0, le=10000`    |

> `success_probability`（Binomial / Bernoulli / Geometric / NegativeBinomial）は
> 既存の `gt=0, le=1` のまま変更なし。

### 注意事項

- これは**破壊的変更**。既存データやテストで上限を超える値が使われていないことを確認する。
- `api/tests/` のアサーション（`message` / `details` の完全一致）が変わる場合は合わせて更新する。

---

## 将来候補

- 分布プレビューの API から X 軸範囲のみを返す軽量エンドポイントの追加（UI 初期化用途）。
- 複数分布の比較機能（一括 preview リクエスト）の追加。

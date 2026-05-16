# Frontend Spec

## 目的

フロントエンド(appディレクトリ)の未解消タスクと保留中の設計課題だけを管理する。
実装済みの修正履歴、完了済みタスクはこの文書に残さない。

## 運用ルール

- 未実装・未修正の項目だけを記載する。
- 実装完了を確認した項目はこの文書から削除する。
- フロントエンド単独で完結しない項目は、依存する API / Rust / Tauri 側の変更も併記する。
- リファクタリング項目は、未解消のものだけを残す。

## 現行の前提

- 分析フォームは workspace の work tab として開く。
- 分析成功後は result tab を開き、WorkspaceSurface に戻す。
- data tab / result tab / work tab は workspaceTabs ストアで管理する。
- `currentView` は `"ImportDataFile" | "SaveData" | "Workspace"` の 3 値のみを取る。
- workspace 内で何を表示するかは `activeTabId` のみが決定する。

## 未修正 backlog

### 1. 分析画面の UI 密度調整

- [open] 詳細オプションが多い分析画面は、初期表示をよりコンパクトに保つレイアウトへ寄せる。
- [open] 14 inch 前後の画面で、主要操作と必須入力がスクロール過多にならない状態を目標とする。

対象候補:

- Linear Regression
- Statistical Test
- 今後オプションが増える分析フォーム

### 3. Linear Regression の列指定 UI 改善

- [open] 選択済みの列と未選択の列の状態差を、より直感的に分かる UI にする。
- [open] 役割ごとの誤選択防止を強める。
- [open] 説明変数、被説明変数、補助オプションの関係が一画面で把握しやすい構成に見直す。

### 4. FilterColumnForm の型整理

- [open] `FilterColumnForm` では `form as unknown as FilterFormType` が残っている。
- [open] `ReactFormExtendedApi` 周辺の型付けを整理し、二重キャストを削除する。

対象:

- `app/src/components/organisms/Dialog/ColumnOperationForms/FilterColumnForm.tsx`

## E2E backlog

### 1. ファイル削除フロー

- [open] ImportDataFile のファイル選択タブで、削除確認ダイアログ、削除完了、一覧再読込までを E2E で確認する。
- [open] 可能なら削除不可ケースも追加で検証する。

### 2. 相関行列のテーブル作成

- [open] 相関行列フォームの実行後、新テーブルがサイドバーに追加されることを E2E で確認する。
- [open] result tab が開くことも確認対象に含める。

### 3. 仮説検定の正常系

- [open] 仮説検定フォームの実行後、result tab に検定統計量と p 値が表示されることを E2E で確認する。

## 実装計画: 分布プレビュー（DistributionPreview）

### 概要

パラメータをスライダーで操作しながら確率分布の形状変化をリアルタイムに確認できる、
統計学習向けのインタラクティブ可視化ツール。Plotly.js を使用。

### 配置

- AppBar に独立した **「可視化」メニュー** を新設する。
  - 初期項目: 「分布プレビュー」のみ。
  - 将来の教育用ビジュアライゼーション（信頼区間シミュレーション等）も同メニューに追加する。
- シミュレーション系フォームからもアクセス可能にする（下記「コンテキスト引き継ぎ」参照）。

### WorkFeatureKey

`"DistributionPreview"` を新規追加する。

### 対象分布

FIXED・SEQUENCE（確率分布ではない）は除外する。

| 区分     | 対象分布（9 + 6 種）                                                                      |
| -------- | ----------------------------------------------------------------------------------------- |
| 連続分布 | uniform, exponential, normal, gamma, beta, weibull, lognormal, chi_square, f_distribution |
| 離散分布 | binomial, bernoulli, poisson, geometric, hypergeometric, negative_binomial                |

### グラフ表示仕様

| 区分     | PDF / PMF           | CDF / CMF           |
| -------- | ------------------- | ------------------- |
| 連続分布 | 折れ線グラフ（PDF） | 折れ線グラフ（CDF） |
| 離散分布 | 棒グラフ（PMF）     | 棒グラフ（CMF）     |

- PDF/PMF と CDF/CMF はタブ切り替えで表示（1 画面に 1 グラフ）。
- グラフタイトルは分布名を表示する。
- X 軸: 確率変数 x、Y 軸: 密度 / 確率 / 累積確率。
- 連続分布の X 軸範囲: バックエンドで 0.5〜99.5 パーセンタイルの範囲を計算して返す。
- 離散分布の X 軸範囲: PMF > 1e-6 となる整数範囲をバックエンドで計算して返す。

### UI 構成（WorkspaceTab 内のレイアウト）

左右 2 ペイン構成。

**左ペイン（コントロール）**

1. 分布カテゴリタブ: 「連続」「離散」（`CreateSimulationDataTable` と同じタブ構成）
2. 分布種類選択: ラジオタググループ（`RadioTagGroup` 流用）
3. パラメータスライダー: 分布切り替え時に動的に切り替わる
   - 各パラメータに スライダー + 数値直接入力フィールドを併設
   - スライダー操作後 300ms デバウンスで API 呼び出し
   - スライダー範囲は各パラメータの合理的なデフォルト範囲（フロントエンド側で定数定義）
4. 表示関数タブ: 「PDF / PMF」「CDF / CMF」

**右ペイン（グラフ）**

- Plotly.js グラフ（`react-plotly.js` を使用）
- API ロード中はスケルトンローダー表示
- API エラー時はエラーアラート表示

### スライダー パラメータ範囲（フロントエンド定数）

**連続分布**

| 分布           | パラメータ             | 最小値 | 最大値 | デフォルト | ステップ |
| -------------- | ---------------------- | -----: | -----: | ---------: | -------: |
| uniform        | low                    |    -10 |     10 |          0 |      0.1 |
| uniform        | high                   |    -10 |     10 |          1 |      0.1 |
| exponential    | scale_parameter        |    0.1 |     10 |          1 |      0.1 |
| normal         | mean                   |    -10 |     10 |          0 |      0.1 |
| normal         | standard_deviation     |    0.1 |      5 |          1 |      0.1 |
| gamma          | shape_parameter        |    0.1 |     10 |          2 |      0.1 |
| gamma          | scale_parameter        |    0.1 |     10 |          1 |      0.1 |
| beta           | alpha                  |    0.1 |     10 |          2 |      0.1 |
| beta           | beta                   |    0.1 |     10 |          5 |      0.1 |
| weibull        | shape_parameter        |    0.1 |     10 |        1.5 |      0.1 |
| weibull        | scale_parameter        |    0.1 |     10 |          1 |      0.1 |
| lognormal      | log_mean               |     -3 |      3 |          0 |      0.1 |
| lognormal      | log_standard_deviation |    0.1 |      3 |          1 |      0.1 |
| chi_square     | degrees_of_freedom     |      1 |     30 |          5 |        1 |
| f_distribution | numerator_df           |      1 |     50 |          5 |        1 |
| f_distribution | denominator_df         |      1 |    100 |         10 |        1 |

**離散分布**

| 分布              | パラメータ           | 最小値 | 最大値              | デフォルト | ステップ |
| ----------------- | -------------------- | -----: | ------------------- | ---------: | -------: |
| binomial          | trial_count          |      1 | 100                 |         10 |        1 |
| binomial          | success_probability  |   0.01 | 0.99                |        0.5 |     0.01 |
| bernoulli         | success_probability  |   0.01 | 0.99                |        0.5 |     0.01 |
| poisson           | rate                 |    0.1 | 30                  |          5 |      0.1 |
| geometric         | success_probability  |   0.01 | 0.99                |        0.3 |     0.01 |
| hypergeometric    | population_size      |     10 | 200                 |         50 |        1 |
| hypergeometric    | success_count        |      1 | ≤ population_size ★ |         20 |        1 |
| hypergeometric    | sample_size          |      1 | ≤ population_size ★ |         10 |        1 |
| negative_binomial | target_success_count |      1 | 50                  |          5 |        1 |
| negative_binomial | success_probability  |   0.01 | 0.99                |        0.5 |     0.01 |

★ success_count / sample_size のスライダー上限は population_size の現在値に動的に追従する。

### コンテキスト引き継ぎ

シミュレーション系フォームから現在選択中の分布 + パラメータを引き継いでプレビュータブを開く。

引き継ぎ元:

- `SimulationColumnEditDialog`（シミュレーションデータ生成フォームの列設定ダイアログ）内に「分布プレビュー」ボタンを追加
- `AddSimulationColumnForm`（列右クリック→シミュレーション列追加）内に「分布プレビュー」ボタンを追加

引き継ぎ方法: `openWorkTab` に `initialValues`（`distributionType` + `distributionParams`）を渡し、
DistributionPreview の `draftValues` として初期化する。

### API 仕様

**エンドポイント**: `POST /api/distribution/preview`（新規）

`api/economicon/utils/algorithms/simulation.py` の流用ではなく、`scipy.stats` を使った
解析的な PDF/CDF 計算とする（サンプリング不要のため、高速・高精度）。

**リクエストボディ**:

```json
{
  "distribution": { "type": "normal", "mean": 0.0, "standard_deviation": 1.0 },
  "x_count": 200
}
```

- `distribution`: 既存の `DistributionConfig` スキーマを流用。
- `x_count`: グラフの解像度（デフォルト 200、離散分布は整数点のため上限値 = 整数の個数）。

**レスポンス（連続分布の例）**:

```json
{
  "is_discrete": false,
  "x": [
    /* float のリスト */
  ],
  "y_density": [
    /* PDF 値 */
  ],
  "y_cumulative": [
    /* CDF 値 */
  ]
}
```

**レスポンス（離散分布の例）**:

```json
{
  "is_discrete": true,
  "x": [
    /* int のリスト */
  ],
  "y_density": [
    /* PMF 値 */
  ],
  "y_cumulative": [
    /* CMF 値 */
  ]
}
```

### 実装スコープ（フロントエンド）

| 対象                             | 変更内容                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------- |
| `workspaceTabs.ts`               | `WorkFeatureKey` に `"DistributionPreview"` を追加                              |
| `workspaceTabs.ts` (constants)   | `WORK_TAB_ENTRIES` に `DistributionPreview` を追加                              |
| `WorkspaceSurface.tsx`           | `WORK_TAB_COMPONENTS` に `<DistributionPreview />` を追加                       |
| `AppBar.tsx`                     | 「可視化」メニューを新設し `DistributionPreview` workTab を開くアクションを追加 |
| `DistributionPreview.tsx`        | 新規コンポーネント（左右ペイン・スライダー・Plotly.js）                         |
| `SimulationColumnEditDialog.tsx` | 「分布プレビュー」ボタンを追加                                                  |
| `AddSimulationColumnForm.tsx`    | 「分布プレビュー」ボタンを追加                                                  |
| `SimulationColumnConfig.tsx`     | χ²・F 分布を連続分布タブに追加                                                  |
| `constants/simulation.ts`        | χ²・F 分布のパラメータ定数・デフォルト値を追加                                  |
| i18n                             | 「可視化」メニュー名・DistributionPreview 内の文言・χ² / F 分布の表示名を追加   |

### 実装スコープ（バックエンド）

| 対象        | 変更内容                                                                        |
| ----------- | ------------------------------------------------------------------------------- |
| `schemas/`  | `DistributionPreviewRequestBody` / `DistributionPreviewResult` スキーマを追加   |
| `services/` | `DistributionPreview` サービスを追加（`scipy.stats` で PDF/CDF/PMF/CMF を計算） |
| `routers/`  | `/api/distribution/preview` エンドポイントを追加                                |
| i18n        | エラーメッセージ等を追加（必要な場合）                                          |

### Phase 3 — `stores/workspaceTabs.ts` 拡張

**対象ファイル**: workspaceTabs.ts

| 変更箇所                 | 内容                                                                   |
| ------------------------ | ---------------------------------------------------------------------- |
| `WorkFeatureKey`         | `"DistributionPreview"` を追加                                         |
| `openWorkTab` シグネチャ | 第 3 引数に `initialValues?: unknown` を追加（コンテキスト引き継ぎ用） |
| `openWorkTab` 実装       | 新規タブ作成時に `initialValues` があれば `draftValues` にセット       |

> **設計判断**: `SimulationColumnEditDialog` / `AddSimulationColumnForm` から「分布プレビュー」を開く際、現在の分布 + パラメータを `initialValues` として渡します。既存タブを再アクティブにする場合は `initialValues` を無視します（既存の `openWorkTab` の挙動を継承）。

---

### Phase 4 — `constants/workspaceTabs.ts` 拡張

**対象ファイル**: workspaceTabs.ts

`WORK_TAB_ENTRIES` に 1 エントリを追加します。

```ts
{ featureKey: "DistributionPreview", titleKey: "HeaderMenu.DistributionPreview" }
```

---

### Phase 5 — i18n キー追加 (ja.json / en.json)

| キー                                       | 日本語           | 英語                 |
| ------------------------------------------ | ---------------- | -------------------- |
| `HeaderMenu.Visualization`                 | 可視化           | Visualization        |
| `HeaderMenu.DistributionPreview`           | 分布プレビュー   | Distribution Preview |
| `AddSimulationColumnForm.chi_square`       | カイ二乗分布     | Chi-Square           |
| `AddSimulationColumnForm.f_distribution`   | F 分布           | F-Distribution       |
| `AddSimulationColumnForm.DegreesOfFreedom` | 自由度           | Degrees of Freedom   |
| `AddSimulationColumnForm.NumeratorDf`      | 分子自由度       | Numerator df         |
| `AddSimulationColumnForm.DenominatorDf`    | 分母自由度       | Denominator df       |
| `DistributionPreview.*`                    | ページ内の全文言 | 同上                 |

---

### Phase 6 — AppBar.tsx に「可視化」メニュー追加

**対象ファイル**: AppBar.tsx

`menus` 配列の末尾（線形回帰メニューの後）に新メニューを追加します。

```ts
{
  id: "visualization",
  menuName: t("HeaderMenu.Visualization"),
  items: [
    {
      id: "distribution-preview",
      label: t("HeaderMenu.DistributionPreview"),
      handleSelect: () => handleOpenWorkTab("DistributionPreview", t("HeaderMenu.DistributionPreview")),
    },
  ],
}
```

---

### Phase 7 — バックエンド `POST /api/distribution/preview` 追加

`new-api-endpoint` スキルに従い、以下 4 ステップで実装します。

| ファイル（新規）                   | 内容                                                                                                                                                                         |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schemas/distribution_preview.py`  | `DistributionPreviewRequestBody`（`distribution: DistributionConfig`, `x_count: int = 200`）+ `DistributionPreviewResult`（`is_discrete`, `x`, `y_density`, `y_cumulative`） |
| `services/distribution_preview.py` | `scipy.stats` で PDF/CDF（連続）・PMF/CMF（離散）を計算。X 軸範囲をバックエンドで決定（連続: 0.5〜99.5 パーセンタイル、離散: PMF > 1e-6 の整数範囲）                         |
| `routers/distribution.py`          | `POST /api/distribution/preview`                                                                                                                                             |
| `main.py`                          | 新ルーターを登録                                                                                                                                                             |

その後 `pnpm gen:all` を再実行してフロントエンドの型を同期します。

---

### Phase 8 — WorkspaceSurface.tsx に `DistributionPreview` 登録

**対象ファイル**: WorkspaceSurface.tsx

- `import { DistributionPreview } from "@/components/pages/DistributionPreview"` を追加
- `WORK_TAB_COMPONENTS` に `DistributionPreview: <DistributionPreview />` を追加

`DistributionPreview` は自身で `useWorkspaceTabsStore` から `draftValues` を読むため、**型ガード関数は不要**（`JoinTable` と同じ "static" 扱い）。

---

### Phase 9 — `DistributionPreview.tsx` 新規作成 (最大実装)

**対象ファイル**: `app/src/components/pages/DistributionPreview.tsx`（新規）

#### レイアウト

```
<PageLayout>
  <div class="grid grid-cols-[320px_1fr] gap-4 h-full">
    ←左ペイン（コントロール）  右ペイン（グラフ）→
  </div>
</PageLayout>
```

#### 左ペイン

1. **分布カテゴリタブ** — `Tabs` / `TabsList` / `TabsTrigger`（連続 / 離散）
2. **分布選択** — `RadioTagGroup`（`CONTINUOUS_DIST_TYPES` / `DISCRETE_DIST_TYPES`）
3. **パラメータスライダー** — 分布切り替え時に動的レンダリング
   - `<input type="range">` + `<InputText>` の組み合わせ（双方向同期）
   - `DIST_PREVIEW_PARAM_RANGES` から min / max / step を読む
   - `hypergeometric` の `successCount` / `sampleSize` 上限は `populationSize` の現在値に動的追従
   - 300ms デバウンス → API 呼び出し
4. **表示関数タブ** — 「PDF / PMF」「CDF / CMF」

#### 右ペイン

- `react-plotly.js` の `<Plot>` コンポーネント
  - 連続分布: `scatter` トレース（mode: `"lines"`）
  - 離散分布: `bar` トレース
- ローディング中: スケルトン（`Loader2` アイコン + `animate-spin`）
- エラー時: `ErrorAlert`

#### カスタム hook

`useDistributionPreview(distribution, functionType)`:

- `invoke("preview_distribution", { body })` をコール
- `loading` / `error` / `result` を返す

#### コンテキスト引き継ぎ

- `useWorkspaceTabsStore` で active tab の `draftValues` を読み、型 narrow 後に初期分布・パラメータとして使用

---

### Phase 10 — 「分布プレビュー」ボタンを既存フォームに追加

| 対象ファイル                   | 変更                                                                    |
| ------------------------------ | ----------------------------------------------------------------------- |
| SimulationColumnEditDialog.tsx | ダイアログフッターに「分布プレビュー」ボタン（`variant="outline"`）追加 |
| AddSimulationColumnForm.tsx    | フォーム末尾に「分布プレビュー」ボタン追加                              |

どちらも `openWorkTab("DistributionPreview", ..., { distributionType, distributionParams })` を呼びます。

---

### 実装順序と依存関係

```
Phase 0 (gen:all)
   ↓
Phase 1 (simulation.ts) + Phase 5 (i18n) ← 並列可
   ↓
Phase 2 (distributionPreview.ts) + Phase 3 (store) + Phase 4 (tabs) ← 並列可
   ↓
Phase 6 (AppBar) + Phase 7 (backend + gen:all) ← 並列可
   ↓
Phase 8 (WorkspaceSurface) + Phase 9 (DistributionPreview) ← Phase 7 の型が必要
   ↓
Phase 10 (ボタン追加)

---

## 将来検討

### Plotly.js を使った統計ビジュアライゼーション（第 2 弾以降）

- [future] 「可視化」メニューへの追加候補として保持する。
- [future] 信頼区間シミュレーション、回帰係数の分布、一致性・不偏性の教育用シミュレーション。
- [future] 既存の業務用チャート機能（ChartView）とは切り分けて検討する。
```

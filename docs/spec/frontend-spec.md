# Analysis Workspace Spec

## 目的

分析ワークスペースまわりの未解消タスクと保留中の設計課題だけを管理する。
実装済みの修正履歴、完了済みタスク、詳細すぎる実装メモはこの文書に残さない。

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

| 区分     | 対象分布（7 + 6 種）                                                       |
| -------- | -------------------------------------------------------------------------- |
| 連続分布 | uniform, exponential, normal, gamma, beta, weibull, lognormal              |
| 離散分布 | binomial, bernoulli, poisson, geometric, hypergeometric, negative_binomial |

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
| i18n                             | 「可視化」メニュー名・DistributionPreview 内の文言を追加                        |

### 実装スコープ（バックエンド）

| 対象        | 変更内容                                                                        |
| ----------- | ------------------------------------------------------------------------------- |
| `schemas/`  | `DistributionPreviewRequestBody` / `DistributionPreviewResult` スキーマを追加   |
| `services/` | `DistributionPreview` サービスを追加（`scipy.stats` で PDF/CDF/PMF/CMF を計算） |
| `routers/`  | `/api/distribution/preview` エンドポイントを追加                                |
| i18n        | エラーメッセージ等を追加（必要な場合）                                          |

### 未決定事項

- [ ] スライダーのパラメータ範囲（各分布の上下限値）はフロントエンド定数で管理するか、API レスポンスに含めるか。
- [ ] `react-plotly.js` を新規依存として追加するか、生の Plotly.js を使うか（バンドルサイズ考慮）。

---

## 将来検討

### Plotly.js を使った統計ビジュアライゼーション（第 2 弾以降）

- [future] 「可視化」メニューへの追加候補として保持する。
- [future] 信頼区間シミュレーション、回帰係数の分布、一致性・不偏性の教育用シミュレーション。
- [future] 既存の業務用チャート機能（ChartView）とは切り分けて検討する。

# Frontend Spec

Economicon フロントエンド（`app/` ディレクトリ）の設計仕様書。
Claude Code などの AI エージェントがコード生成・レビュー・変更を行う際の参照ドキュメント。

---

## 1. 技術スタック

| 種別              | ライブラリ                                                    |
| ----------------- | ------------------------------------------------------------- |
| UI フレームワーク | React 19 / Vite 7（SWC）                                      |
| デスクトップ      | Tauri 2                                                       |
| パッケージ管理    | pnpm                                                          |
| スタイリング      | Tailwind CSS 4 / Radix UI Primitives                          |
| クラス結合        | `cn()`（clsx + tailwind-merge）                               |
| フォーム          | @tanstack/react-form + Zod                                    |
| 状態管理          | Zustand                                                       |
| テーブル表示      | @tanstack/react-table + react-virtual                         |
| ドラッグ操作      | @dnd-kit/core                                                 |
| 国際化            | i18next / react-i18next                                       |
| API クライアント  | Orval 生成（`src/api/`）                                      |
| アイコン          | Lucide React                                                  |
| テスト            | Vitest（Unit）/ Playwright（E2E）                             |
| コンパイラ最適化  | React Compiler（原則として手動 `useMemo`/`useCallback` 不要） |

---

## 2. アーキテクチャ概要

### 2.1 通信レイヤー

```
React コンポーネント
   ↓ Orval 生成クライアント (src/api/endpoints.ts)
   ↓ api-gateway.ts（client.post / client.get / client.fetch_binary）
   ↓ Tauri invoke("proxy_request" / "get_files" / "get_os_info" 等)
   ↓ Rust プロキシ（X-Auth-Token ヘッダーを自動付与）
   ↓ FastAPI サイドカー
```

- **`fetch` / `axios` 禁止**。バックエンド通信は必ず Tauri `invoke` を経由する
- バイナリデータ（Apache Arrow）は `client.fetch_binary` → `invoke("proxy_binary_request")` を使用
- ファイルシステム操作は `src/api/bridge/tauri-commands.ts` の関数を使用

### 2.2 起動シーケンス

```
App.useEffect:
  1. getAuthToken()      ← Rust 側で起動時生成、確認まで後続ブロック
  2. getOsInfo()         ← OS 種別・パス区切り文字を取得
  3. waitForServer()     ← FastAPI ヘルスチェック（最大 150 秒、500ms 間隔）
  4. getSettings()       ← アプリ設定をロード
  5. getFiles()          ← ファイル一覧を初期化
  6. getTableList()      ← テーブル一覧を初期化
  → currentView を "ImportDataFile" に設定
```

### 2.3 ページ遷移

`currentView`（`useCurrentPageStore`）で制御する。3 値のみ。

| currentView        | 表示コンポーネント   | 用途                         |
| ------------------ | -------------------- | ---------------------------- |
| `"ImportDataFile"` | `<ImportDataFile>`   | ファイル選択・インポート画面 |
| `"SaveData"`       | `<SaveData>`         | データエクスポート画面       |
| `"Workspace"`      | `<WorkspaceSurface>` | テーブル・分析・結果閲覧画面 |

---

## 3. ディレクトリ構造（アトミックデザイン）

```
src/
├── api/
│   ├── bridge/
│   │   ├── api-gateway.ts      # Tauri invoke ラッパー（client.get/post/…）
│   │   └── tauri-commands.ts   # ファイル操作・OS 情報・認証トークン取得
│   ├── endpoints.ts            # Orval 生成 API クライアント（手書き禁止）
│   ├── model/                  # Orval 生成型定義（手書き禁止）
│   └── zod/                    # Orval 生成 Zod スキーマ（手書き禁止）
├── components/
│   ├── atoms/                  # 最小 UI（ロジックなし）
│   ├── molecules/              # atoms の組み合わせ（軽度のロジック可）
│   ├── organisms/              # ビジネスロジック・Store 可
│   ├── templates/              # レイアウトコンポーネント
│   └── pages/                  # ページコンポーネント（ルートに近い）
├── constants/                  # 定数（SCREAMING_SNAKE_CASE）
├── hooks/                      # カスタム React Hooks
├── i18n/                       # i18next 設定・翻訳ファイル
├── lib/
│   ├── dialog/                 # confirm / message ダイアログヘルパー
│   └── utils/                  # 汎用ユーティリティ
├── stores/                     # Zustand ストア
├── test/                       # テスト共通ユーティリティ・フィクスチャ
├── tests/                      # Vitest 統合テスト
└── types/
    └── commonTypes.ts          # アプリ固有型定義
```

> **Orval 生成ファイル（`src/api/model/` / `src/api/zod/`）は絶対に手書きしない・再定義しない。**
> API スキーマ変更時は `pnpm gen:all` を実行して自動再生成する。

---

## 4. 状態管理（Zustand ストア一覧）

| ストア                    | ファイル                    | 管理対象                                                        |
| ------------------------- | --------------------------- | --------------------------------------------------------------- |
| `useCurrentPageStore`     | `stores/currentPage.ts`     | `currentView`（3 値）のナビゲーション状態                       |
| `useWorkspaceTabsStore`   | `stores/workspaceTabs.ts`   | ワークスペースのタブ一覧・アクティブ ID                         |
| `useTableListStore`       | `stores/tableList.ts`       | インメモリテーブル名の配列                                      |
| `useTableInfosStore`      | `stores/tableInfos.ts`      | テーブルメタ情報（列定義・行数・アクティブ状態）                |
| `useTableChunkStore`      | `stores/tableChunkStore.ts` | Arrow IPC バイナリのチャンクキャッシュ（LRU, 上限 20 チャンク） |
| `useAnalysisResultsStore` | `stores/analysisResults.ts` | 分析結果サマリー一覧・アクティブ結果詳細                        |
| `useSettingsStore`        | `stores/settings.ts`        | アプリ設定（言語・テーマ・パス）+ OS 情報                       |
| `useFilesStore`           | `stores/files.ts`           | ファイル一覧・現在のディレクトリパス                            |
| `useLoadingStore`         | `stores/loading.ts`         | グローバルローディングオーバーレイ状態                          |
| `useConfirmDialogStore`   | `stores/confirmDialog.ts`   | 確認ダイアログ（Promise ベース）                                |
| `useMessageDialogStore`   | `stores/messageDialog.ts`   | メッセージダイアログ                                            |
| `useExplainerDialogStore` | `stores/explainerDialog.ts` | 用語説明ダイアログ                                              |

### セレクタ形式（必須）

```ts
// ✅ 正しい
const value = useStore((s) => s.value);

// ❌ 禁止（オブジェクト全体を購読するとすべての変更で再レンダーが起きる）
const { value } = useStore();
```

---

## 5. ワークスペースタブシステム

### タブの種別

| kind       | 型                   | ID パターン         | 説明                   |
| ---------- | -------------------- | ------------------- | ---------------------- |
| `"data"`   | `WorkspaceDataTab`   | `data:{tableName}`  | テーブルデータ表示     |
| `"result"` | `WorkspaceResultTab` | `result:{resultId}` | 分析結果表示           |
| `"work"`   | `WorkspaceWorkTab`   | `work:{featureKey}` | 分析フォーム・操作画面 |

- **work タブ**はフィーチャーキーごとに 1 枚のみ（再オープンすると既存タブにフォーカス）
- `dirty` フラグが `true` のときにタブを閉じようとすると確認ダイアログが表示される
- `draftValues` / `committedValues` でフォーム値の保持と変更検知を行う

### 全 WorkFeatureKey（フォームとその対応エンドポイント）

| WorkFeatureKey              | 画面タイトル（i18n キー）          | 呼び出し API                                     |
| --------------------------- | ---------------------------------- | ------------------------------------------------ |
| `JoinTable`                 | `HeaderMenu.JoinTable`             | `POST /table/create-join`                        |
| `UnionTable`                | `HeaderMenu.UnionTable`            | `POST /table/create-union`                       |
| `CreateSimulationDataTable` | `HeaderMenu.DataGeneration`        | `POST /table/create-simulation-data`             |
| `CalculationView`           | `HeaderMenu.Calculate`             | `POST /column/calculate`                         |
| `DescriptiveStatistics`     | `HeaderMenu.BasicStatistics`       | `POST /statistics/descriptive`                   |
| `ConfidenceIntervalView`    | `HeaderMenu.ConfidenceInterval`    | `POST /statistics/confidence-interval`           |
| `StatisticalTestView`       | `HeaderMenu.HypothesisTest`        | `POST /statistics/test`                          |
| `CorrelationMatrix`         | `HeaderMenu.CorrelationMatrix`     | `POST /statistics/create-correlation-table`      |
| `GroupStatistics`           | `HeaderMenu.GroupStatistics`       | `POST /statistics/create-group-statistics-table` |
| `PlotView`                  | `HeaderMenu.Plot`                  | `POST /table/fetch-plot-data`                    |
| `DistributionPreview`       | `HeaderMenu.DistributionPreview`   | `POST /distribution/preview`                     |
| `LinearRegressionForm`      | `HeaderMenu.OrdinaryLeastSquares`  | `POST /analysis/regression`（method=ols）        |
| `WLSRegressionForm`         | `HeaderMenu.WeightedLeastSquares`  | `POST /analysis/regression`（method=wls）        |
| `LogitRegressionForm`       | `HeaderMenu.LogitAnalysis`         | `POST /analysis/regression`（method=logit）      |
| `ProbitRegressionForm`      | `HeaderMenu.ProbitAnalysis`        | `POST /analysis/regression`（method=probit）     |
| `TobitRegressionForm`       | `HeaderMenu.TobitAnalysis`         | `POST /analysis/regression`（method=tobit）      |
| `IVRegressionForm`          | `HeaderMenu.InstrumentalVariables` | `POST /analysis/regression`（method=iv）         |
| `FERegressionForm`          | `HeaderMenu.FixedEffects`          | `POST /analysis/regression`（method=fe）         |
| `RERegressionForm`          | `HeaderMenu.RandomEffects`         | `POST /analysis/regression`（method=re）         |
| `ConfidenceIntervalSim`     | `HeaderMenu.ConfidenceIntervalSim` | `POST /simulation/confidence-interval`           |
| `AsymptoticNormality`       | `HeaderMenu.AsymptoticNormality`   | `POST /simulation/asymptotic-normality`          |
| `Consistency`               | `HeaderMenu.Consistency`           | `POST /simulation/consistency`                   |
| `Unbiasedness`              | `HeaderMenu.Unbiasedness`          | `POST /simulation/unbiasedness`                  |

### 分析フォーム成功後のフロー

```
分析フォーム（work タブ）→ API 呼び出し成功
  → openResultTab(detail)   ワークスペースに result タブを開く
  → closeActiveWorkTab()    作業中の work タブを閉じる
```

---

## 6. 主要コンポーネント

### 6.1 ページコンポーネント（`src/components/pages/`）

| コンポーネント              | 説明                                                          |
| --------------------------- | ------------------------------------------------------------- |
| `MainView`                  | `currentView` に応じて 3 画面を切り替えるルートコンポーネント |
| `WorkspaceSurface`          | タブバー + タブコンテンツの Workspace 本体                    |
| `LeftSideMenu`              | サイドバー（テーブル一覧 / 分析結果一覧のペイン切り替え）     |
| `ImportDataFile`            | ファイルブラウザ + インポート設定ダイアログ                   |
| `SaveData`                  | エクスポート先選択 + フォーマット設定                         |
| `AnalysisResultPreview`     | result タブ内で結果種別に応じた表示コンポーネントを選択       |
| `Calculation`               | 計算列追加フォーム                                            |
| `DescriptiveStatistics`     | 記述統計フォーム                                              |
| `ConfidenceIntervalView`    | 信頼区間計算フォーム                                          |
| `StatisticalTestView`       | 統計的検定フォーム                                            |
| `CorrelationMatrix`         | 相関行列フォーム                                              |
| `GroupStatistics`           | GroupBy 統計フォーム                                          |
| `PlotView`                  | プロットビュー（散布図・ヒストグラム等）                      |
| `DistributionPreview`       | 確率分布プレビュー                                            |
| `JoinTable`                 | テーブル結合フォーム                                          |
| `UnionTable`                | テーブルユニオンフォーム                                      |
| `CreateSimulationDataTable` | シミュレーションデータテーブル作成                            |
| `ConfidenceIntervalSim`     | 信頼区間シミュレーション                                      |
| `AsymptoticNormality`       | 漸近正規性シミュレーション                                    |
| `Consistency`               | 一致性シミュレーション                                        |
| `Unbiasedness`              | 不偏性シミュレーション                                        |

### 6.2 回帰分析フォーム（`src/components/organisms/Form/`）

| コンポーネント         | 対応 method | 備考                                    |
| ---------------------- | ----------- | --------------------------------------- |
| `LinearRegressionForm` | `ols`       | `CommonRegressionForm` を基底として使用 |
| `WLSRegressionForm`    | `wls`       | 重み列追加フィールド                    |
| `LogitRegressionForm`  | `logit`     | 限界効果・正則化オプション              |
| `ProbitRegressionForm` | `probit`    | 同上                                    |
| `TobitRegressionForm`  | `tobit`     | 打ち切り値フィールド                    |
| `IVRegressionForm`     | `iv`        | 操作変数・内生変数フィールド            |
| `FERegressionForm`     | `fe`        | 個体 ID・時点列フィールド               |
| `RERegressionForm`     | `re`        | 同上                                    |

### 6.3 分析結果コンポーネント（`src/components/organisms/Result/`）

| コンポーネント                | `resultType`             | 表示内容                                                            |
| ----------------------------- | ------------------------ | ------------------------------------------------------------------- |
| `RegressionResult`            | `regression`             | 係数表（coef/std_err/t/p/CI）・適合度指標・診断列追加・テキスト出力 |
| `DescriptiveStatisticsResult` | `descriptive_statistics` | 統計量テーブル                                                      |
| `ConfidenceIntervalResult`    | `confidence_interval`    | 推定値・CI 下限・上限                                               |
| `StatisticalTestResult`       | `statistical_test`       | 検定統計量・p 値・効果量                                            |
| `TobitDiagnostics`            | —                        | Tobit モデル専用診断情報（`RegressionResult` に埋め込み）           |

サイドバーの分析結果一覧は `resultType` でグルーピングし、下記の順序で表示する。
`descriptive_statistics` → `confidence_interval` → `regression` → `statistical_test` → `did` → `rdd` → `heckman`

### 6.4 テーブル表示（`VirtualTable`）

- **仮想スクロール**: `react-virtual` による行仮想化（全行を DOM に生成しない）
- **チャンクキャッシュ**: `tableChunkStore` に Apache Arrow IPC バイナリを 500 行単位でキャッシュ
  LRU で上限 20 チャンク（10,000 行）まで保持。列操作後は自動的にキャッシュを無効化する
- **列ドラッグ並び替え**: `@dnd-kit/core` で実装。ドロップ後に `POST /column/move` を呼び出す
- **カラム幅自動計算**: 列名の全角/半角を区別して適切な初期幅を算出
- **コンテキストメニュー**: 列ヘッダー右クリックで `ColumnOperationDialog` を開く

### 6.5 列操作ダイアログ（`ColumnOperationDialog`）

ヘッダー右クリックで開く。以下の操作を提供する：

- 削除 / 名前変更 / 型変換 / 変換（log/power/root）
- ダミー変数追加 / ラグ・リード列追加 / シミュレーション列追加 / パネル時点列追加
- フィルタ適用（新テーブル生成）

---

## 7. フォーム規約

### 7.1 使用ライブラリ

**@tanstack/react-form** + **Zod** を組み合わせる。
React Hook Form は使用しない（混入禁止）。

### 7.2 Zod スキーマ

- フォームバリデーション用 Zod スキーマは `src/api/zod/`（Orval 生成）から import する
- 同等スキーマを手書きで再定義することは禁止

### 7.3 フォーム送信時のローディング制御

`useFormSubmitting` フックを使用する（各フォームで繰り返し実装しない）。

```ts
useFormSubmitting(form.state.isSubmitting, onIsSubmittingChange);
```

### 7.4 `useFormSubmitting` フック

`form.state.isSubmitting` の変化を `onIsSubmittingChange` コールバックに伝播する。
work タブ親コンポーネントがローディングオーバーレイの表示制御に使用する。

---

## 8. API 通信規約

### 8.1 エラーハンドリング

Tauri `invoke` が throw するエラーは文字列形式の場合がある。`src/lib/utils/apiError.ts` のユーティリティを使用する。

```ts
// catch ブロックで使用
const message = extractApiErrorMessage(error, t("FallbackError"));

// API レスポンスの code !== "OK" 判定
const message = getResponseErrorMessage(response, t("FallbackError"));
```

### 8.2 エラー表示

エラーメッセージは `showMessageDialog()` で表示する。
小さなインラインエラーよりもダイアログが標準的なパターン。

### 8.3 Tauri Commands（ファイル操作系）

`src/api/bridge/tauri-commands.ts` で定義する。

| 関数                  | Rust コマンド     | 用途                           |
| --------------------- | ----------------- | ------------------------------ |
| `getFiles(path)`      | `get_files`       | ディレクトリ内ファイル一覧取得 |
| `getFilesSafe(path)`  | `get_files`       | getFiles のエラー無視版        |
| `deleteFile(path)`    | `delete_file`     | ファイル削除                   |
| `canDeleteFile(path)` | `can_delete_file` | 削除可能か判定                 |
| `getOsInfo()`         | `get_os_info`     | OS 種別・パス区切り文字取得    |
| `getAuthToken()`      | `get_auth_token`  | 認証トークン取得（起動時のみ） |

### 8.4 型安全性

- `any` 使用禁止。`invoke` 結果は Zod で型検証すること（または Orval 生成クライアント経由で呼び出す）
- `enum` 禁止。Union `type` または `const` オブジェクトを使う
- `erasableSyntaxOnly` 準拠：コンストラクタパラメータプロパティは使用しない

---

## 9. i18n 規約

- JSX 内に日本語・英語の文字列を直接ハードコード禁止
- `react-i18next` の `useTranslation()` → `t("Key")` を使用する
- 翻訳ファイル: `src/i18n/` 配下

---

## 10. スタイリング規約

- Tailwind CSS のクラスは必ず `cn()` で結合する

```ts
// ✅ 正しい
cn("base-class", isError && "border-red-500", className);

// ❌ 禁止
"base-class " + (isError ? "border-red-500" : "") + " " + className;
```

- `dark:` プレフィックスを使ってダークモード対応する
- テーマ切り替えは `<html>` 要素の `class="dark"` で制御（`App.tsx` の `useEffect` が管理）

---

## 11. テスト規約

### 11.1 Vitest（ユニット・コンポーネント）

- jsdom 環境でコンポーネントレンダリングを検証する
- テスト命名: `test("[機能]_[シナリオ]")`

### 11.2 Playwright（E2E）

- テスト: `e2e/*.spec.ts`
- `data-testid` 属性を適宜付与して要素を特定する
- 一連のストーリー（ファイルインポート → 分析 → 結果確認）を検証する

### 11.3 テスト知見（Radix UI）

**問題**: `fireEvent.click()` は Radix UI のインタラクティブ要素（`TabsTrigger` 等）に機能しない。
Radix UI は `onPointerDown` + `onClick` の組み合わせで状態遷移する。

**解決策**: `@testing-library/user-event` の `userEvent.setup().click()` を使用する。

```ts
const user = userEvent.setup();
// ❌ fireEvent.click(screen.getByText("Tab"))
await user.click(screen.getByText("Tab")); // ✅
```

- `userEvent.setup()` は各テストケース内で毎回呼ぶ（`beforeEach` で共有しない）

### 11.4 テスト知見（制御済みラジオ入力）

**問題**: `checked={value === selected}` で制御する `<input type="radio">` に `userEvent.click()` が機能しない場合がある。

**解決策**: `fireEvent.click(screen.getByDisplayValue(value))` を使用する。

```ts
// ❌ await userEvent.click(screen.getByRole("radio", { name: "有効" }));
fireEvent.click(screen.getByDisplayValue("true")); // ✅
```

---

## 12. 命名規則

| 対象                   | 規則                 | 例                 |
| ---------------------- | -------------------- | ------------------ |
| コンポーネントファイル | PascalCase           | `InputText.tsx`    |
| コンポーネント         | PascalCase           | `InputText`        |
| 型・インターフェース   | PascalCase + `Type`  | `UserDataType`     |
| 関数・hooks            | camelCase            | `useTableLoader`   |
| 定数                   | SCREAMING_SNAKE_CASE | `MAX_CACHE_CHUNKS` |
| デフォルトエクスポート | 禁止                 | —                  |

---

## 13. 未修正 backlog

### 1. 分析画面の UI 密度調整

- [open] 詳細オプションが多い分析画面は、初期表示をよりコンパクトに保つレイアウトへ寄せる
- [open] 14 inch 前後の画面で、主要操作と必須入力がスクロール過多にならない状態を目標とする

対象候補: Linear Regression / Statistical Test / 今後オプションが増える分析フォーム

### 2. Linear Regression の列指定 UI 改善

- [open] 選択済みの列と未選択の列の状態差を、より直感的に分かる UI にする
- [open] 役割ごとの誤選択防止を強める
- [open] 説明変数・被説明変数・補助オプションの関係が一画面で把握しやすい構成に見直す

### 3. FilterColumnForm の型整理

- [open] `FilterColumnForm` では `form as unknown as FilterFormType` が残っている
- [open] `ReactFormExtendedApi` 周辺の型付けを整理し、二重キャストを削除する

対象: `app/src/components/organisms/Dialog/ColumnOperationForms/FilterColumnForm.tsx`

---

## 14. E2E backlog

### 1. ファイル削除フロー

- [open] `ImportDataFile` のファイル選択タブで、削除確認ダイアログ → 削除完了 → 一覧再読込まで確認

### 2. 相関行列のテーブル作成

- [open] 相関行列フォーム実行後、新テーブルがサイドバーに追加されることを確認
- [open] result タブが開くことも確認対象に含める

### 3. 仮説検定の正常系

- [open] 仮説検定フォーム実行後、result タブに検定統計量と p 値が表示されることを確認

### 4. プロットビューの正常系

- [open] プロットビュー実行によってプロットが表示されることを確認

### 5. グループ別統計量の正常系

- [open] グループ別統計量実行後、新規テーブルが表示されることを確認

### 6. 分布プレビューの正常系

- [open] 分布プレビュー実行によってプロットが表示されることを確認

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

### 4. プロットビューの正常系

- [open] プロットビュー実行によってプロットが表示されることを確認

### 5. グループ別統計量の正常系

- [open] グループ別統計量実行後、新規テーブルが表示されることを確認

### 6. 分布プレビューの正常系

- [open] 分布プレビュー実行によってプロットが表示されることを確認

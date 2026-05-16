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
- 分析成功後は result tab を開き、DataPreview に戻す。
- data tab / result tab / work tab は workspaceTabs ストアで管理する。
- `currentView` と `activeTabId` はまだ併存しており、責務分離は未完了である。

## 未修正 backlog

### 1. 画面状態管理の整理

#### 現状の問題

| 問題                            | 詳細                                                                                                                          |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `currentView` が肥大化          | 16 値を取るが、JoinTable 等 work tab 系はすべて `WorkspaceSurface` を返すだけで値が表示に直結していない                       |
| 常に2つ同時更新が必要           | `setCurrentView` 46 箇所・`activateTab` 18 箇所の大部分がペアで呼ばれており、不整合リスクがある                               |
| WorkspaceSurface に暗黙の副作用 | `currentView === "DataPreview"` 検知の useEffect と `suppressWorkTabCleanupRef` フラグで state が暗黙に変化し、デバッグが困難 |

#### 方針

**方針 1: `currentView` を「シェル画面の識別子」に絞る**

現在 16 値ある `CurrentPageValue` を `"ImportDataFile" | "SaveData" | "Workspace"` の 3 値に削減する。

- `"DataPreview"` / `"AnalysisResultPreview"` は `"Workspace"` に統合する。
- `JoinTable` / `DescriptiveStatistics` 等 work tab 系の値はすべて廃止する。
- ワークスペース内で何を表示するかは `activeTabId` のみが決定する。

```
Before: currentView = "JoinTable"
After:  currentView = "Workspace",  activeTabId = "work:JoinTable"
```

**方針 2: 用途別アクション関数を `workspaceTabs` ストアに集約する**

`setCurrentView` + `activateTab`（または `openXxxTab`）を個別に呼ぶ実装を廃止し、以下のアクションに寄せる。

| アクション                          | 置き換える操作                                             | `currentView` の変化   |
| ----------------------------------- | ---------------------------------------------------------- | ---------------------- |
| `navigateToShell("ImportDataFile")` | `setCurrentView("ImportDataFile")`                         | → `"ImportDataFile"`   |
| `navigateToShell("SaveData")`       | `setCurrentView("SaveData")`                               | → `"SaveData"`         |
| `navigateToWorkspace()`             | ワークスペースへの復帰時の `setCurrentView("DataPreview")` | → `"Workspace"`        |
| `openDataTab(tableName)`            | `openDataTab` + `setCurrentView("DataPreview")` のペア     | → `"Workspace"` (内包) |
| `openResultTab(detail)`             | `openResultTab` + `setCurrentView("DataPreview")` のペア   | → `"Workspace"` (内包) |
| `openWorkTab(featureKey, title)`    | `openWorkTab` + `setCurrentView(featureKey)` のペア        | → `"Workspace"` (内包) |

`openXxxTab` 系は内部で `navigateToWorkspace()` を呼ぶことで `currentView` の同期を自動化する。

**方針 3: WorkspaceSurface の暗黙フォールバックを削除する**

- `currentView === "DataPreview"` をトリガーにした useEffect を廃止する。
- `suppressWorkTabCleanupRef` フラグも不要になるため削除する。
- work tab のクローズ後フォールバックは `closeTab()` ストアロジック内に移動する。

#### 実装ステップ

```
Step 1: currentView.ts の型変更
  - CurrentPageValue を "ImportDataFile" | "SaveData" | "Workspace" の 3 値に変更する。
  - setCurrentView を navigateToShell / navigateToWorkspace に分割する。
  - 旧 setCurrentView はエクスポートしない。

Step 2: workspaceTabs.ts の openXxxTab 修正 + closeActiveWorkTab 追加
  - openDataTab / openResultTab / openWorkTab の内部で
    currentView ストアの navigateToWorkspace() を自動呼び出しするようにする。
    （Zustand の getState() を使うことでストア間の循環参照を回避する）
  - closeActiveWorkTab() アクションを新規追加する。
    - activeTabId が "work:*" でない場合は何もしない。
    - work tab を tabs から削除し、直前の non-work tab に activeTabId をフォールバックする。
    - この戻り先ロジックで suppressWorkTabCleanupRef + useEffect を代替する。

Step 3: MainView の PAGE_COMPONENTS 簡略化
  - Record<CurrentPageValue, ...> 型の PAGE_COMPONENTS を削除する。
  - 3 値に対応するシンプルな条件分岐（if / switch）に整理する。

Step 4: WorkspaceSurface の useEffect 整理
  - currentView 依存のフォールバック useEffect（L166-208）を削除する。
  - suppressWorkTabCleanupRef を削除する。
  - handleCloseTab 内の suppressWorkTabCleanupRef.current = true も削除する。
  - handleCloseTab 内の setCurrentView("DataPreview") を navigateToWorkspace() に置換する。
  - isWorkFeatureKey は useEffect 削除後に参照なしになるため、
    constants/workspaceTabs.ts から削除する。

Step 5: 各コンポーネントの呼び出し箇所修正
  - setCurrentView("DataPreview") → navigateToWorkspace() に置換する（約 30 箇所）。
  - openXxxTab + setCurrentView のペアを openXxxTab 単体に置換する。
  - シェル遷移は navigateToShell(xxx) に統一する。
  - 分析成功後に setCurrentView("DataPreview") を呼んでいる箇所は
    closeActiveWorkTab() に置換する（work tab を明示的に閉じるシグナルに変更）。
    対象: LinearRegressionForm / CorrelationMatrix / DescriptiveStatistics /
          StatisticalTestView / GroupStatistics / JoinTable / UnionTable /
          CreateSimulationDataTable / Calculation / ConfidenceIntervalView 等

Step 6: テストの修正
  - WorkspaceSurface.test.tsx: currentView を work tab 値にセットしている箇所（約 8 箇所）を
    "Workspace" に変更する。
  - LinearRegressionForm.test.tsx L270: toBe("DataPreview") → toBe("Workspace") に変更し、
    closeActiveWorkTab が呼ばれたことの検証に切り替える。
  - ImportDataFile.test.tsx L368: toBe("DataPreview") → toBe("Workspace") に変更する。
  - ConfidenceIntervalForm.test.tsx L93: setup の "ConfidenceIntervalView" → "Workspace" に変更する。
```

#### 完了条件

- workspace 内の data / result / work 表示が tab state だけで決まる。
- シェル画面遷移と workspace 内タブ切り替えの責務が分離される。
- `CurrentPageValue` の値が 3 値（`"ImportDataFile" | "SaveData" | "Workspace"`）に削減されている。
- `setCurrentView` と `activateTab` を別々に呼ぶ実装が存在しない。
- `suppressWorkTabCleanupRef` と `currentView` 依存の useEffect が WorkspaceSurface に存在しない。
- 全ユニットテストがグリーンである。

### 2. 分析画面の UI 密度調整

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

## 将来検討

### Plotly.js を使った統計ビジュアライゼーション

- [future] 統計教育向けの可視化は別枠の将来課題として扱う。
- [future] 現時点では仕様を詳細化しすぎず、次の 2 系統だけを候補として保持する。

候補:

- 分布シミュレーションのプレビュー
- 信頼区間、回帰係数分布、一致性などの教育用シミュレーション

補足:

- 既存の業務用チャート機能とは切り分けて検討する。
- 配置先と優先度が確定した段階で、この節を詳細化する。

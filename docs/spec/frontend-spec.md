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

- [open] `currentView` と `activeTabId` の二重管理を解消する。
- [open] workspace 内表示は `activeTabId` を正とし、ImportDataFile / SaveData / Workspace のようなシェル画面だけを別状態で持つ構成へ整理する。
- [open] `setCurrentView` と `activateTab` を個別に呼ぶ実装を減らし、用途別アクションへ寄せる。

完了条件:

- workspace 内の data / result / work 表示が tab state だけで決まる。
- シェル画面遷移と workspace 内タブ切り替えの責務が分離される。

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

# Analysis Workspace Spec

## 目的

分析画面まわりの UI 仕様と残課題を 1 つの文書に集約する。現時点で実装済みか未修正かを明示し、未修正項目を今後の作業単位として管理する。

## 運用ルール

- 未修正の項目はこの文書の「未修正 backlog」に残す。
- 項目を実装したら、まず「今回修正済み」に移す。
- リリース前または次の整理時に、「今回修正済み」に残っている項目は削除する。
- フロントエンドだけで完結しない項目は、依存する API 変更も併記する。

## 現行仕様

### 1. 分析フォームと結果表示

- 分析の入力画面は work tab か単独ページで開く。
- 分析が成功したら、基本フローは API 実行 → getAnalysisResult → result tab を開く → fetchSummaries → DataPreview へ戻す。
- 分析結果の表示ガワは AnalysisResultPanel / AnalysisResultPreview に統一する。
- descriptive statistics / confidence interval / statistical test は result tab 表示を正とする。

### 2. タブ操作

- 明示的に work tab を閉じたとき、他の work tab を連鎖的に閉じない。
- 分析完了やキャンセルで DataPreview に戻る場合だけ、必要に応じて work tab をクローズまたは fallback tab に切り替える。
- data tab / result tab は workspaceTabs ストアで一元管理する。

## 今回修正済み

- [fixed] WorkspaceSurface: アクティブな work tab を閉じても、残っている別の work tab を自動クローズしない。
- [fixed] DescriptiveStatistics: 計算成功後は画面内に結果表を出さず、result tab を開いて DataPreview に戻る。

## 未修正 backlog

- [pending] Basic Statistics を単独ページではなく work tab として開く。
- [pending] Correlation Matrix を単独ページではなく work tab として開く。
- [pending] 基本分析系フォームの empty state と no-data 文言を統一する。
- [pending] 基本統計量の初期選択統計量を見直す。現状は全統計量が初期選択。
- [pending] 基本統計量に min / max / skewness / kurtosis を追加する。API 列挙型と Orval 生成物の同期が前提。
- [pending] OutputResultDialog の resultKind 分岐を switch ベースへ整理し、非回帰系の見通しを上げる。
- [pending] 詳細オプションが多い分析画面は、初期表示をコンパクトに保つレイアウトへ寄せる。

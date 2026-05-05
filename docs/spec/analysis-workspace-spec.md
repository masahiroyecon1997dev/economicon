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
- Basic Statistics / Correlation Matrix / Confidence Interval / Hypothesis Test は基本分析メニューから work tab として開く。
- 既存の RegressionView 内部タブは、この分析画面タブ統一の現在スコープには含めない。必要なら次フェーズで別件として扱う。

### 2. タブ操作

- 明示的に work tab を閉じたとき、他の work tab を連鎖的に閉じない。
- 分析完了やキャンセルで DataPreview に戻る場合だけ、必要に応じて work tab をクローズまたは fallback tab に切り替える。
- data tab / result tab は workspaceTabs ストアで一元管理する。

## 今回修正済み

- [fixed] WorkspaceSurface: アクティブな work tab を閉じても、残っている別の work tab を自動クローズしない。
- [fixed] DescriptiveStatistics: 計算成功後は画面内に結果表を出さず、result tab を開いて DataPreview に戻る。
- [fixed] Basic Statistics: 基本分析メニューから work tab として開き、WorkspaceSurface 上で他の分析画面と同じ導線に揃えた。
- [fixed] Correlation Matrix: 基本分析メニューから work tab として開き、Basic Statistics と同じタブ導線に揃えた。
- [fixed] Basic Statistics API: min / max / skewness / kurtosis を追加し、resultData に columnNameList / statisticOrder を含める shape に揃えた。
- [fixed] DescriptiveStatisticsResult: statisticOrder / columnNameList を優先し、旧 resultData では canonical order にフォールバックして表示順を決める。
- [fixed] DescriptiveStatistics i18n: min / max / skewness / kurtosis の ja / en ラベルを追加し、kurtosis は excess kurtosis と表示文言を合わせた。
- [fixed] NoTables empty state: Basic Statistics / Correlation Matrix / Confidence Interval / Hypothesis Test の 4 画面で、共通文言と ImportDataFile 導線を先に揃えた。
- [fixed] Basic Statistics: 初期選択統計量を全選択から標準セットへ変更した。
- [fixed] Analysis empty state: NoEligibleColumns / LoadingColumns も 4 画面で共通レイアウトへ寄せ、NoTables を含めて action bar 付きの共通部品に統一した。

## API拡張仕様

### 基本統計量の追加候補

- 追加候補は min / max / skewness / kurtosis。
- 既存の range / variance / population_variance は残す。
- kurtosis は excess kurtosis として扱う前提で仕様を固定する。
- 非適用の統計量は null を返す方針を維持する。

### エンドポイント方針

- POST /api/statistics/descriptive は維持する。
- POST の成功レスポンスは resultId のみを返す現行方針を維持する。
- 詳細結果は getAnalysisResult で取得する前提を維持する。

### resultData 拡張案

- descriptive_statistics の resultData に columnNameList と statisticOrder を追加する。
- statistics は列名ごとの辞書を維持し、追加統計量を同じレベルで返す。

想定 shape:
### 分析画面 empty state 仕様

- Basic Statistics / Correlation Matrix / Confidence Interval / Hypothesis Test の 4 画面は、NoTables / LoadingColumns / NoEligibleColumns を共通レイアウトで表示する。
- NoTables は AnalysisEmptyState 系の共通文言を使い、ImportDataFile へ遷移する主 action と cancel action を共通 action bar で表示する。
- LoadingColumns は同じカード骨格を使い、列情報の取得中であることを明示する。追加 action は持たない。
- NoEligibleColumns は同じカード骨格を使い、タイトルと補助ヒントは共通キー、必要列の説明は画面個別キーで補足する。
- テーブル未選択時は従来どおり Select のプレースホルダを使い、専用 empty state は出さない。

### empty state 文言ルール

- データ未投入: ワークスペースに分析対象データがないことを明示し、ファイル取込へ誘導する。
- 列読み込み中: 列情報を読み込んでいる途中であることだけを簡潔に示す。
- 対象列なし: 選択テーブルには必要な列がないことを明示し、別テーブル選択または前処理を案内する。
- 文言は AnalysisEmptyState を共通骨格とし、画面差分は各画面キーの detail/hint に閉じ込める。

- 1 は画面横断で同じ見た目、同じ文言構造、同じ誘導アクションに揃える。
- 2 は画面ごとに条件が違うため本文は個別化してよいが、レイアウト・トーン・補助説明の出し方は共通化する。
- empty state の文言は、単なる否定文だけで終わらせず、次に何をすればよいかを 1 文で示す。
- この整理ではまだ全画面共通コンポーネント化を必須にしない。まず見た目と文言ルールを揃え、差分が固まった段階で共通化を判断する。

### 4 画面の現状棚卸し

1. Basic Statistics

- ワークスペースにテーブルが 0 件なら、共通 NoTables empty state を表示して ImportDataFile へ誘導する。
- テーブル未選択時は列エリア自体を出さず、空状態メッセージは出していない。
- テーブル選択後は LoadingColumns と NoColumns をテキストで表示する。
- 初期選択統計量は全選択ではなく、count / mean / median / std_dev / min / max の標準セットを使う。

2. Correlation Matrix

- ワークスペースにテーブルが 0 件なら、共通 NoTables empty state を表示して ImportDataFile へ誘導する。
- テーブル未選択時は列ペイン内に SelectData をプレースホルダ風テキストで出す。
- テーブル選択後に対象列が 0 件だと NoColumns を列ペイン内に表示する。

3. Confidence Interval

- ワークスペースにテーブルが 0 件なら、共通 NoTables empty state を表示して ImportDataFile へ誘導する。
- テーブル未選択時の専用 empty state はなく、Select のプレースホルダのみ。
- 列が 0 件でも NoColumns や補助説明は出ず、列 Select が disabled になるだけ。
- LoadingColumns 相当の表示も現状は持っていない。

4. Hypothesis Test

- ワークスペースにテーブルが 0 件なら、共通 NoTables empty state を表示して ImportDataFile へ誘導する。
- サンプルごとに table / column を持つため、空状態が行単位に分散している。
- テーブル未選択時の専用 empty state はなく、各 Select のプレースホルダのみ。
- テーブル選択後に数値列が 0 件だと、対象列の下に NoColumns を補助文として出す。

### empty state の共通キー案

- 名前空間は仮で AnalysisEmptyState とする。
- まずは 4 画面共通で次の骨格キーを持つ。

1. AnalysisEmptyState.NoTablesTitle
2. AnalysisEmptyState.NoTablesDescription
3. AnalysisEmptyState.NoTablesAction
4. AnalysisEmptyState.NoEligibleColumnsTitle
5. AnalysisEmptyState.NoEligibleColumnsDescription
6. AnalysisEmptyState.NoEligibleColumnsHint
7. AnalysisEmptyState.LoadingColumns

- NoTables 系は「分析対象データがまだない」状態を表す共通キーとし、画面別に言い換えない。
- NoEligibleColumns 系はレイアウト骨格を共通化するためのベース文言として使い、どの条件を満たしていないかは画面個別キーで補足する。
- LoadingColumns は Basic Statistics の既存キーを起点に、他画面でも同じトーンへ寄せる候補とする。

### empty state の画面個別キー案

- 画面ごとの差は「必要列の条件説明」だけに寄せる。
- 個別キーは仮で <Screen>.EmptyState.\* に寄せる。

1. DescriptiveStatistics.EmptyState.NoEligibleColumnsDetail
2. CorrelationMatrix.EmptyState.NoEligibleColumnsDetail
3. ConfidenceIntervalView.EmptyState.NoEligibleColumnsDetail
4. StatisticalTestView.EmptyState.NoEligibleColumnsDetail

- Basic Statistics は「このテーブルに集計可能な列がありません。別のテーブルを選ぶか、前処理で対象列を追加してください。」を基準文とする。
- Correlation Matrix は「このテーブルに相関計算に必要な数値列がありません。」を基準文とする。
- Confidence Interval は「このテーブルに信頼区間を計算できる列がありません。」を基準文とする。
- Hypothesis Test は「このテーブルに検定に使える数値列がありません。」を基準文とする。
- Hypothesis Test はサンプル行ごとの文脈があるため、必要なら SampleRowNoEligibleColumnsDetail のような派生キーを追加してよい。

### 導入順の提案

1. Basic Statistics / Correlation Matrix の NoEligibleColumns を共通レイアウトへ寄せる。
2. Confidence Interval / Hypothesis Test に不足している NoEligibleColumns と LoadingColumns の表示を追加する。
3. 最後に key 名の整理と共通コンポーネント化の要否を判断する。

### empty state 文言ルール

- データ未投入: ワークスペースに分析対象データがないことを明示し、ファイル取込またはサンプルデータ準備へ誘導する。
- 対象列なし: 選択テーブルには必要な列がないことを明示し、別テーブル選択または前処理を案内する。
- 文言は NoData, NoColumns, EmptyState のようなキーの乱立を避け、画面共通の骨格に寄せて整理する。
- 次の UI 整理では、各画面の空状態を棚卸しして、共通キー候補と画面個別キー候補を分けて定義する。

## 未修正 backlog

- [pending] OutputResultDialog の resultKind 分岐を switch ベースへ整理し、非回帰系の見通しを上げる。
- [pending] 詳細オプションが多い分析画面は、初期表示をコンパクトに保つレイアウトへ寄せる。

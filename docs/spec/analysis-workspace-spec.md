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
- 回帰分析の workspace 導線は RegressionView を介さず、LinearRegressionForm の work tab と result tab に統一する。

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
```json
{
	"tableName": "sales",
	"columnNameList": ["revenue", "employees"],
	"statisticOrder": [
		"count",
		"mean",
		"std_dev",
		"min",
		"max",
		"skewness",
		"kurtosis"
	],
	"statistics": {
		"revenue": {
			"count": 120,
			"mean": 103.2,
			"std_dev": 14.8,
			"min": 74.0,
			"max": 151.0,
			"skewness": 0.41,
			"kurtosis": -0.62
		}
	}
}
```

### フロントエンドへの影響

- Orval 生成 enum に min / max / skewness / kurtosis を追加する。
- DescriptiveStatisticsResult は statisticOrder 優先で列順を描画する。
- i18n に Stat_min / Stat_max / Stat_skewness / Stat_kurtosis を追加する。

## UI 具体仕様

### DescriptiveStatisticsResult の表示順

- 行方向の列順は resultData.columnNameList を最優先で使う。
- resultData.columnNameList がない旧結果では statistics のキー順を使う。
- 列方向の統計量順は resultData.statisticOrder を最優先で使う。
- resultData.statisticOrder がない旧結果では、次の canonical order を使う。

canonical order:

1. count
2. null_count
3. null_ratio
4. mean
5. median
6. mode
7. variance
8. population_variance
9. std_dev
10. min
11. max
12. range
13. iqr
14. skewness
15. kurtosis

- canonical order にない将来の統計量キーは、既知キーの後ろに API から来た順で追加表示する。
- テーブル描画時は、表示対象の統計量キーを 1 列目の辞書構造から推測しない。resultData.statisticOrder または canonical order で明示的に決める。
- 古い resultData でも列を欠落させないことを優先する。順序が不明でも、statistics 内に存在するキーはすべて描画対象に含める。

### DescriptiveStatisticsResult の i18n

- 統計量ラベルは DescriptiveStatistics.Stat_<statKey> に統一する。
- 追加キーは次で固定する。
- ja: Stat_min=最小値、Stat_max=最大値、Stat_skewness=歪度、Stat_kurtosis=超過尖度
- en: Stat_min=Min、Stat_max=Max、Stat_skewness=Skewness、Stat_kurtosis=Excess Kurtosis
- kurtosis は API の excess kurtosis と表示文言を一致させるため、英語は Kurtosis ではなく Excess Kurtosis を使う。
- 翻訳キーが存在しない未知の統計量は、表示崩れを避けるため statKey の生値をヘッダーに出してよい。翻訳未定義で列自体を消さない。

### 互換性の扱い

- 新規に保存される descriptive_statistics 結果は、columnNameList と statisticOrder を常に持つ前提でよい。
- 既存の保存済み結果タブや import 済み結果は、columnNameList / statisticOrder が欠ける可能性を考慮して描画する。
- 結果表示コンポーネント側で migration は行わず、描画時フォールバックで吸収する。

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

### 回帰分析 work tab 方針

- 現行の workspace タブ導線では、LinearRegressionForm の work tab は WorkspaceSurface から直接フォーム本体を描画する。
- 回帰分析の成功後は、RegressionView 内部タブに切り替えず、他分析と同じく result tab を開いて DataPreview に戻す。
- RegressionView コンポーネントは削除し、回帰分析の導線を workspace タブへ一本化する。

### OutputResultDialog 方針

- OutputResultDialog は resultKind の discriminated union を入力とし、switch ベースで regression と non-regression を分岐する。
- non-regression 系の output payload は resultKind ごとの helper で一元化する。
- LeftSideMenu からの出力導線も同じ union shape に寄せ、descriptive statistics / confidence interval / statistical test / regression を同じ方法で開く。

## 未修正 backlog

- [pending] 詳細オプションが多い分析画面は、初期表示をコンパクトに保つレイアウトへさらに寄せる。

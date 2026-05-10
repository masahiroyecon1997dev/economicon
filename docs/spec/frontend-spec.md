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
- Workspace 表示中の data / result / work の中身は activeTabId を唯一の正として扱い、currentView は workspace 外のシェル画面切り替えに限定するのが整理方針である。

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
- [fixed] Correlation Matrix / Group Statistics: 新規テーブル作成成功時に tableInfo と tableList を同時更新し、LeftSideBar とテーブル一覧へ即時反映するように揃えた。
- [fixed] Analysis forms: code !== OK と catch の両方でサーバー message を優先表示する方針に揃え、Correlation Matrix / Group Statistics の newTableName はフォーム入力名に置換して表示するようにした。
- [fixed] LinearRegressionForm: 他の分析フォームと同じ title / description ヘッダーを追加した。
- [fixed] StatisticalTestView: 14 inch 画面を想定し、検定タイプ行・サンプルカード・オプション領域の余白を圧縮して縦方向の情報密度を改善した。
- [fixed] WorkspaceSurface: タブのドラッグ&ドロップ並び替えを追加し、Alt+Shift+ArrowLeft / ArrowRight でも左右移動できるようにした。
- [fixed] Group Statistics: 2 ステップ Wizard を実装し、Step 2 を Role Assignment Matrix ベースに再構成した。列検索、役割の排他制御、summary、統計量選択、出力データ名を同一ステップに集約した。

### WorkspaceSurface タブ D&D 実装メモ

- タブのドラッグ開始時は、ネイティブ D&D を成立させるため DataTransfer に workspace tab 用 MIME type と tab id を格納し、effectAllowed は move に固定する。
- ドロップ先の tab 本体と drop slot は dragOver ごとに dropEffect=move を明示し、WebView2 上で禁止マークにならないことを正とする。
- 並び替え処理のソースは React state の draggedTabId だけに依存せず、drop 時は DataTransfer に入っている tab id からも復元できるようにする。
- jsdom の fireEvent だけではネイティブ D&D の成立条件を十分に再現できないため、ユニットテストでは DataTransfer を明示モックし、必要なら将来的に E2E でも補完する。

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

- 統計量ラベルは DescriptiveStatistics.Stat\_<statKey> に統一する。
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

### ImportDataFile のファイル削除仕様

- 対象画面は ImportDataFile の「ファイル選択」タブとし、ドラッグ&ドロップタブには削除導線を置かない。
- 削除処理は API を経由せず、Tauri invoke から Rust 側の OS ファイル操作で完結させる。
- 削除対象は現在一覧に表示されている通常ファイルのうち、Economicon が扱うデータ拡張子 `.csv` / `.xlsx` / `.xls` / `.parquet` に限定する。ディレクトリには削除アイコンを表示しない。
- FileListTable には行右端の action 列を追加し、削除可能ファイルにだけ削除アイコンを表示する。行本体クリックの import / ディレクトリ移動と、削除アイコンクリックの挙動は分離する。
- 削除アイコン押下時は、Rust 側の事前チェック command で削除可否を判定する。判定 NG の場合は確認ダイアログへ進めず、「削除できません」ダイアログを表示する。
- 「削除できません」ダイアログでは、少なくとも次をユーザー向け文言で案内する。
- 権限不足で削除できない。
- 他プロセスが使用中で削除できない。
- 対象ファイルが既に存在しない、またはパスが無効になっている。
- 事前チェック OK の場合だけ削除確認ダイアログを開く。確認ダイアログには対象ファイル名を表示し、「この削除は元に戻せません」を明記する。
- 削除確認ダイアログで OK を押したら、Rust 側の削除 command を実行して即時削除する。ごみ箱への移動は行わない。
- 削除実行中は二重送信を防ぐため、確認ダイアログの OK を loading 状態にする。
- 事前チェック後から実削除までの間に状態が変わり削除失敗した場合は、完了ダイアログではなく「削除できません」ダイアログを再表示して終了する。
- 削除成功時は「削除が完了しました」ダイアログを表示し、ユーザーが閉じた後に現在ディレクトリを再読込してファイル一覧を更新する。
- 再読込は既存の getFiles(directoryPath) を使い、一覧から削除済みファイルが消えた状態を正とする。現在ディレクトリが失効していた場合は既存の safe reload 方針にフォールバックする。
- 本機能の主目的は、不要なデータファイルを ImportDataFile 画面から即座に整理できることと、E2E テストで保存済みファイルを後片付けしやすくすることにある。

## 未修正 backlog

- [pending] ImportDataFile のファイル選択タブに Rust ベースのファイル削除導線を追加し、削除不可 / 確認 / 完了ダイアログと一覧再読込まで実装する。
- [pending] 詳細オプションが多い分析画面は、初期表示をコンパクトに保つレイアウトへさらに寄せる。
- [pending] Linear Regression の列指定 UI は、選択済み状況の可視化と役割ごとの誤選択防止を強めたレイアウトへ更新する。
- [pending] currentView と activeTabId の二重管理を整理し、workspace 内表示は activeTabId、アプリ全体画面は shellView 相当の単純な状態に責務分離する。

### currentView / activeTabId 整理案

- currentView は ImportDataFile / SaveData / Workspace のようなシェル画面専用の状態へ縮小し、DataPreview / LinearRegressionForm / CorrelationMatrix など workspace 内の view 種別は持たない。
- WorkspaceSurface の描画分岐は activeTabId から導出した activeTab.kind を唯一の正とし、data tab は表、result tab は結果、work tab はフォームを表示する。
- 画面から直接 setCurrentView と activateTab を別々に呼ぶ形はやめ、showImportView / showSaveView / activateDataTab / activateResultTab / activateWorkTab のような用途別アクションへ寄せる。
- インポート成功時は tableInfo 追加後に新規 data tab を必ず activate し、その後に workspace シェルへ戻す。DataPreview へ戻すだけで activeTabId を放置する状態は許容しない。
- 段階的移行では、まず currentView を shellView 相当へ改名して値を縮小し、その後に WorkspaceSurface 配下の setCurrentView("DataPreview") / setCurrentView(workFeatureKey) 呼び出しを tab activation API へ置換する。

---

### E2E テスト追加

#### ファイル削除フロー E2E

- シナリオ: ファイル保存またはサンプル配置で削除対象の `.csv` / `.parquet` を用意 → ImportDataFile のファイル選択タブで削除アイコンをクリック → 確認ダイアログで OK → 完了ダイアログを閉じる → 一覧から対象ファイルが消えていることを確認
- 確認ポイント: 削除確認ダイアログに「この削除は元に戻せません」が表示されること / 完了ダイアログ表示後に一覧再読込が走ること / 削除済みファイルが同ディレクトリ一覧に残らないこと
- 異常系: 権限不足または使用中ファイルを用意できる場合は、「削除できません」ダイアログが表示され、対象ファイルが残ることを確認する
- 配置案: 既存の import / save 導線に近い E2E へ追記、または新規 `app/e2e/04-file-delete.spec.ts`

#### 相関行列テーブル作成 E2E

- シナリオ: ファイルインポート → 相関行列フォームで列を複数選択 → 実行 → 結果テーブル名がサイドバーに追加表示されることを確認
- 確認ポイント: 新テーブルがサイドバーの一覧に現れる / result tab が開くこと
- 配置案: 既存の `02-parquet-import-statistics-ols.spec.ts` に追記

#### 仮説検定 正常系 E2E

- シナリオ: サンプル CSV インポート → 仮説検定（t 検定）フォームで変数・設定を選択 → 実行 → result tab に検定統計量と p 値が表示されることを確認
- 確認ポイント: result tab が開くこと / 検定統計量・p 値の表示セクションが存在すること
- 配置案: 新規 `app/e2e/04-hypothesis-test.spec.ts`

---

### Plotly.js 統計ビジュアライゼーション

#### 配置方針（要最終確認）

4 種のうち **① 分布シミュレーション** はデータ生成フォームの文脈で使うことを想定。
列編集ダイアログ内のプレビューパネルへの統合を第一案とするが、ダイアログのサイズ・レイアウト変更が必要なため要検討。
**② ③ ④** の教育的シミュレーション図は独立した統計教育ビジュアライゼーションページにまとめ、メインメニューから遷移する方式を第一案とする。

#### ① 分布シミュレーション図

- 内容: データ生成で利用可能な全分布（正規 / 一様 / t / カイ二乗 / F / 二項 / ポアソン など）の PDF / PMF をインタラクティブに表示
- インタラクション: 分布種別セレクタ + 各パラメータのスライダー → リアルタイムで確率密度/質量関数を再描画
- データソース: クライアント側 JS で生成（API 不要）
- 配置案: データ生成の列編集ダイアログ内プレビューパネル（要レイアウト検討）

#### ② 信頼区間の網羅性シミュレーション

- 内容: 真の値 μ を固定し同一設定で CI を 100 本生成、95% が真値を含む様子を可視化
- インタラクション: サンプルサイズ / 信頼水準 / 真のパラメータをスライダーで変更 → 包含率と図を再計算
- データソース: クライアント側 JS で乱数生成

#### ③ 回帰パラメータ分布（CLT・漸近正規性）

- 内容: 同一 DGP で回帰を 100 回繰り返し、β 推定値の分布が正規分布に収束する様子を図示
- インタラクション: サンプルサイズ / 真の β / 誤差分散をスライダーで変更
- データソース: クライアント側 JS で乱数生成

#### ④ 一致性の可視化

- 内容: サンプルサイズを増やしながら β 推定値が真値に収束する様子を折れ線またはアニメーションで表示
- インタラクション: 試行回数 / 真の β をスライダーで変更
- データソース: クライアント側 JS で乱数生成

### Plotly 4 種の仕様

#### ① 分布シミュレーション図

- 内容: データ生成で利用可能な全分布（正規 / 一様 / t / カイ二乗 / F / 二項 / ポアソン など）の PDF / PMF をインタラクティブに表示
- インタラクション: 分布種別セレクタ + 各パラメータのスライダー → リアルタイムで確率密度/質量関数を再描画
- データソース: クライアント側 JS で生成（API 不要）
- 配置: **SimulationColumnEditDialog 内プレビューパネル**（ダイアログレイアウト変更を伴う）→ **フェーズ 1 で実装**

#### ② 信頼区間の網羅性シミュレーション（後回し）

- 内容: 真の値 μ を固定し同一設定で CI を 100 本生成、95% が真値を含む様子を可視化
- インタラクション: サンプルサイズ / 信頼水準 / 真のパラメータをスライダーで変更 → 包含率と図を再計算
- データソース: クライアント側 JS で乱数生成

#### ③ 回帰パラメータ分布（CLT・漸近正規性）（後回し）

- 内容: 同一 DGP で回帰を 100 回繰り返し、β 推定値の分布が正規分布に収束する様子を図示
- インタラクション: サンプルサイズ / 真の β / 誤差分散をスライダーで変更
- データソース: クライアント側 JS で乱数生成

#### ④ 一致性の可視化（後回し）

- 内容: サンプルサイズを増やしながら β 推定値が真値に収束する様子を折れ線またはアニメーションで表示
- インタラクション: 試行回数 / 真の β をスライダーで変更
- データソース: クライアント側 JS で乱数生成

#### 技術メモ

- plotly.js はインストール済み（`plotly.js@3.5.0`、`@types/plotly.js@^3.0.10`）
- ② ③ ④ の配置は未定（後回し）。配置先が決まったときにここを更新する

---

### グループ別基本統計量テーブル作成（フロント実装）

#### 概要

`POST /api/statistics/create-group-statistics-table` は API 実装済み。フロントの実装が未対応。

#### フォーム仕様

| フィールド     | UI 部品               | 備考                                                              |
| -------------- | --------------------- | ----------------------------------------------------------------- |
| 対象テーブル   | Select                | テーブル一覧から選択                                              |
| グループキー列 | VariableSelectorField | 複数選択可。Float32/Float64 列はグレーアウトして選択不可にする    |
| 集計列         | VariableSelectorField | 複数選択可。groupByColumns との重複は不可（重複列は選択不可表示） |
| 統計量         | CheckboxTagGroup      | Basic Statistics と同じ選択 UI・同項目                            |
| 出力テーブル名 | InputText             | 入力必須                                                          |

#### グループキー列の Float 除外実装方針

- `getColumnList` は列ごとに `columnType` を返す
- `useTableColumnLoader` は `numericOnly` フィルタのみ持つため、グループキー列用に **Float 除外フィルタ** を呼び出し側で実装する
  - `columns.filter(col => !col.columnType.includes("Float"))` で除外
  - VariableSelectorField の `columns` props に渡す前にフィルタをかける方式（ `disabled` props を列単位で持たせる拡張は行わない）
- 集計列（statColumns）は全列を渡す（Float も含む）

#### 列の重複バリデーション

- groupByColumns と statColumns に同じ列が含まれる場合はフォームレベルでバリデーションエラーを出す
- API でも弾かれるが、フロントでも即時フィードバックする

#### 結果フロー

- 成功後は新テーブルとして workspaceTabs に追加（`create-correlation-table` と同じフロー）
- サイドバーにテーブルが追加表示され、DataPreview に戻す

#### 配置

- 基本分析メニューから work tab として開く（`GroupStatistics` as `WorkFeatureKey`）
- Correlation Matrix の下に配置予定

#### 型・スキーマ

- Orval 生成の `CreateGroupStatisticsTableRequestBody` / `CreateGroupStatisticsTableResult` を使用
- Zod スキーマは `CreateGroupStatisticsTableBody`（`@/api/zod/statistics/statistics`）を使用
- 手動再定義禁止

---

### 通常グラフビュー（散布図・ヒストグラム・折れ線グラフ）

#### 概要

`fetchPlotData`（Arrow IPC）で取得したデータをフロントで Plotly.js により可視化する。
分析結果として保存しない（work tab 内のみ、閉じたら消える）。

#### データフロー

```
ユーザーが列選択
  → fetchPlotData (Arrow IPC バイナリ)
  → @apache-arrow/es2015-esm で RecordBatch に変換
  → 列データを JS number[] に変換
  → Plotly.react() でチャート更新
```

#### 対応グラフ種別と列選択

| 種別         | X 軸           | Y 軸              | 備考                            |
| ------------ | -------------- | ----------------- | ------------------------------- |
| 散布図       | 数値列（1 列） | 数値列（1 列）    | hover で (x, y) 値を表示        |
| ヒストグラム | 数値列（1 列） | —（自動集計）     | ビン数は UI で調整可（10〜100） |
| 折れ線グラフ | 任意列（1 列） | 数値列（1〜複数） | 時系列・カテゴリ軸にも対応      |

#### 実装方針（3 案から選択）

> **案は別途確認のうえ決定する。** 以下は選択肢の概要：
>
> - **案 A（スプリットパネル）**: 左 30% 設定 + 右 70% グラフ。列変更 → debounce 400ms → 自動再描画。「実行」ボタン不要。探索性が高い。
> - **案 B（縦積み）**: フォーム（上）+「描画する」ボタン + グラフ（下）。既存 work tab パターンに最も近い。
> - **案 C（サブタブ）**: work tab 内に「設定」「グラフ」サブタブ。グラフ全画面表示。

#### 配置

- 基本分析メニューから work tab として開く（`ChartView` as `WorkFeatureKey`）
- Arrow デコードには `apache-arrow` パッケージを使用（インストール要確認）

#### 列制約

- 散布図・ヒストグラムの X 軸: 数値列のみ（`numericOnly: true` を `useTableColumnLoader` に渡す）
- 折れ線グラフの X 軸: 全列（文字列・日付・数値）

---

### Plotly 教育ビジュアライゼーション ① 分布シミュレーション

#### 対象

データ生成の列編集ダイアログ（`SimulationColumnEditDialog`）内にプレビューパネルとして統合。

#### 仕様

- 選択中の分布と現在のパラメータ値に応じた PDF / PMF をリアルタイム描画
- 分布種別セレクタ変更 / パラメータ変更 → 即時再描画（API 不要、クライアント JS で生成）
- 対応分布: 正規 / 一様 / t / カイ二乗 / F / 二項 / ポアソン（データ生成で使用可能な全分布）
- パラメータはスライダーまたは数値入力と連動
- グラフサイズ: ダイアログ内プレビュー領域（高さ約 200px）

#### 実装メモ

- SimulationColumnEditDialog のレイアウト変更が必要（プレビューパネル追加）
- ② 信頼区間 / ③ CLT / ④ 一致性 は後回し（別タスクで実装）

---

## 2026-05 UI/UX 改善レビュー

### 1. WorkspaceSurface タブ並び替え

#### 推奨判断

- 推奨。data tab / result tab / work tab が混在すると横並びの走査コストが上がるため、ユーザー自身で順序を整えられる価値が高い。
- 優先度は「不具合修正の次」。致命的不具合ではないが、分析を複数並行すると効いてくる改善。

#### 期待効果

- 比較したい data tab と result tab を隣接配置できる。
- 作業中の work tab を左に寄せ、参照用の result tab を右に逃がすなど、ユーザーごとの作業流儀に合わせやすい。
- タブが増えたときの「どこに何があるか」の探索コストを減らせる。

#### 導入条件

- ドラッグ開始領域は tab 本体のみとし、close button 押下と競合させない。
- ドロップ位置は挿入インジケータを表示し、入れ替え先を視覚的に明示する。
- active tab は並び替え後も active のまま維持する。
- キーボード操作の代替手段を用意する。最低限、コンテキストメニューまたはショートカットで「左へ移動 / 右へ移動」を持たせる。
- work tab の dirty 状態や data/result/work の kind は順序変更で失わない。

#### 非推奨案

- 自動ソート。テーブル名順や作成順へ勝手に戻ると、ユーザーが作った意味のある並びを壊すため不適。

### 2. 確認した不具合と横断方針

#### LeftSideBar に新規テーブルが出ない問題

- Correlation Matrix と Group Statistics は、成功時に addTableInfo は行っているが addTableName を行っていない。
- LeftSideBar とテーブル一覧の描画ソースは tableList のため、DataPreview は開けてもサイドバーには即時反映されない。
- Join Table / Create Simulation Data Table は addTableInfo と addTableName を両方更新しており、ここが挙動差分になっている。

仕様方針:

- 新規テーブルを生成する画面は、成功時に tableInfo と tableList を同一トランザクションとして更新する。
- 画面遷移前に LeftSideBar に新テーブルが見えている状態を正とする。
- 「DataPreview は開くがサイドバーにない」状態を許容しない。

#### サーバーエラーがダイアログに出ない問題

- Correlation Matrix と Group Statistics は code !== OK 分岐で Error.UnexpectedError を固定表示しており、レスポンスの message を捨てている。
- Confidence Interval も同じパターンを持つ。
- Statistical Test / Descriptive Statistics は catch 側では message を拾えるが、非 OK レスポンスや 2 段目 API 失敗時に汎用エラーへ落ちる箇所がある。
- Calculation / Join Table / Save Data / Linear Regression は getResponseErrorMessage を使う箇所があり、こちらが目指すべき基準。

仕様方針:

- API 呼び出し失敗時の表示優先順位は「response.message > thrown error message > 汎用 fallback」とする。
- 分析フォーム間でエラーダイアログの情報量を揃える。
- 入力項目に紐づくエラーは可能な限りフィールド近傍に出し、ダイアログは横断的または予期しない失敗に限定する。
- message が長い場合でも省略せず表示し、必要ならダイアログ内で折り返す。

### 3. フォーム改善方針

#### Linear Regression Form に title / description を追加する

- 他の分析フォームは PageLayout ヘッダーを持つが、Linear Regression Form は本文から始まるため、画面意図と入力対象が一読で分かりにくい。
- 最低限、タイトル、短い説明、期待する入力の順序をヘッダーで提示する。

ヘッダー要件:

- title: 最小二乗法
- description: 「データ選択 → 被説明変数 / 説明変数指定 → 必要なら詳細オプション」という流れが分かる 1 文にする。
- 他フォームと同じ vertical rhythm を保ち、ヘッダー追加で本文の圧迫が増えすぎないよう余白を抑える。

#### Statistical Test を 14 inch 前提で圧縮する

既定表示目標:

- 1366x768 相当で、1 サンプルまたは 2 サンプルの通常利用時に action bar までスクロールなしで見える。
- 追加サンプルや異常系だけがスクロール対象になる。

レイアウト方針:

- test type と sample action を同一行にまとめる。
- sample card は p-4 / space-y-3 を 1 段階圧縮し、行内ラベルを短く保つ。
- options は常時縦積みせず、2 列グリッドかインライン controls に寄せる。
- 補助説明は初期表示では 1 行要約を優先し、詳細は tooltip または help text に逃がす。
- action bar は下端に安定配置し、スクロール時に見失いにくくする。

### 4. 列指定 UI 案（Group Statistics / Linear Regression 共通）

#### 案 A: Dual List Transfer

- 左に候補列、右に選択済み列を置く定番パターン。
- 役割ごとに枠を分けると、被説明変数 / 説明変数 / グループキー / 集計列の境界が明確になる。
- 列数が多いデータでの一覧性が高い。
- 欠点は横幅を使うため、14 inch では 2 役割までが限界。

#### 案 B: Command Palette + Chips

- 入力欄で列名検索し、候補ポップオーバーから追加、選択済みは chips で保持する。
- 列数が多い環境で最も速く、視認ノイズが少ない。
- OLS の説明変数や Group Statistics の集計列と相性が良い。
- 欠点は、列全体を俯瞰して選びたい初学者にはややブラックボックスになりやすい。

#### 案 C: Role Assignment Matrix

- 行に列名、列に役割を置き、checkbox / radio で役割を割り当てる。
- 「この列はグループキーには使えるが集計列には使わない」といったルールを 1 画面で説明しやすい。
- Group Statistics では最も誤選択を防ぎやすい。
- 欠点は実装と学習コストがやや高い。

#### 案 D: Stepper Assignment

- 1 ステップ目でテーブル選択、2 ステップ目で列役割を決め、3 ステップ目でオプションと出力名を決める。
- 一度に見せる情報量を減らせるため、初学者向けに強い。
- 役割が多い画面でも縦の圧迫を抑えやすい。
- 欠点は、熟練者にとっては往復操作が増える。

推奨順:

1. Group Statistics: 案 C または案 D
2. Linear Regression: 案 B または案 A

### 5. Group Statistics 全体レイアウト案

#### 案 1: 2 ステップ Wizard

- step 1 で「対象テーブル / グループキー / 集計列」、step 2 で「統計量 / 出力名 / 実行」に分ける。
- 入力密度を半分に落とせるため、もっとも整理効果が高い。

#### 案 2: Summary Sidebar 付き 2 ペイン

- 左に入力、右に「選択中の設定要約」を固定表示する。
- どの列を何役割に入れたかを常時確認でき、誤設定を減らせる。

#### 案 3: Preset First

- 先に「平均だけ」「平均+標準偏差」「欠損確認込み」などのプリセットを提示し、その後に微調整させる。
- 初学者は短時間で完了でき、上級者だけが詳細編集へ進める。

#### 案 4: Sentence Builder

- 上部に「sales を region, year でグループ化し、revenue, cost に対して mean, std_dev を計算して sales_grouped を作成」のような文を生成する。
- 入力の意味が自然言語として見えるため、学習者に特に有効。
- 実体 UI は既存部品を流用できるため、見た目の改善効果に対して実装負荷を抑えやすい。

推奨順:

1. 案 1
2. 案 2
3. 案 3
4. 案 4

### 6. 採用案の具体化

#### Linear Regression: 案 B（縦積みフォーム）を採用

- レイアウトは「ヘッダー → データ選択 → 変数選択 → 詳細オプション → 実行」の縦積みフローを維持する。
- 自動実行は行わず、明示的な「分析実行」ボタンで結果を作る。
- 詳細オプションは初期折りたたみとし、初学者には主要入力だけを先に見せる。
- 変数選択は 1 画面内で完結させるが、被説明変数と説明変数の役割境界を視覚的に明確に保つ。
- この案は学習コストが低く、既存 work tab の操作モデルから逸脱しないことを優先する。

実装メモ:

- PageLayout の title / description を常に表示する。
- action bar は画面下端に固定し、スクロールしても実行導線を見失いにくくする。
- 今後の列指定 UI 改善は、縦積み全体構成は維持したまま内部の selector を差し替える方針とする。

#### Group Statistics: 2 ステップ Wizard を採用し、ステップ 2 は案 C 寄りの役割割り当て UI にする

- 全体構成は案 1 の 2 ステップ Wizard を採用する。
- ただし列役割の決定は案 D の単純な逐次選択ではなく、ステップ 2 で案 C の Role Assignment Matrix に寄せる。
- これにより初学者には「段階を踏んで進む分かりやすさ」を残しつつ、慣れたユーザーには役割を一画面でまとめて決められる操作性を提供する。

Step 1:

- 対象テーブルを選択する。
- 選択したテーブルに対して、利用可能列数、グループキーに使えない列、集計対象に使える列の考え方を短い説明で示す。
- 次へ進む条件はテーブル選択完了のみとし、初学者がまず対象データを確定できるようにする。

Step 2:

- 上部に列検索欄を置き、その下に Role Assignment Matrix を表示する。
- 行は列名、列は少なくとも「グループキー」「集計列」の 2 役割を持つ。
- 同一列の二重割り当ては UI 上で禁止し、選択できない理由を見える形で示す。
- Float32 / Float64 列はグループキー列としては disabled 表示にする。
- 画面右側または下部に summary パネルを置き、選択済みグループキー、集計列、統計量、出力データ名を常時確認できるようにする。
- 統計量選択、出力データ名、実行ボタンは同じステップ 2 に配置し、2 ステップのまま完結させる。

操作性ルール:

- 初学者向けに Stepper で進行状況を明示する。
- 慣れたユーザー向けに、ステップ 2 では role assignment と最終設定を往復せずに完了できるようにする。
- Desktop では matrix と summary の 2 ペイン、狭い幅では縦積みへ切り替える。
- 出力データ名には自動候補を入れ、必要な場合だけ編集する方式を基本とする。

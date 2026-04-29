# 分析結果ナビゲーション仕様

## 概要

左サイドメニューを単なるデータ一覧ではなく、データと分析結果を横断して扱うワークスペースナビゲータへ拡張する。

この仕様の目的は次の 3 点である。

1. ユーザーがフォーム画面へ戻らなくても、作成済みの分析結果をすぐ見つけられるようにする。
2. 結果タブを閉じる操作と、サーバ上の分析結果を削除する操作を分離する。
3. 回帰分析、基本統計量、信頼区間に加えて、将来の DID、RDD、検定なども同じ導線に載せられる構造にする。

## ゴール

- 左サイドメニューで データ と 分析結果 を切り替えられる。
- 分析結果は一覧から再オープンできる。
- 分析結果の削除は明示的な削除操作からのみ行う。
- 分析種別が増えても左一覧の構造を大きく変えずに拡張できる。

## 実装状況（2026-04-29）

### 実装済み

- 左サイドメニューで データ と 分析結果 を切り替えられる
- 中央領域で データタブ と 分析結果タブ を同じグローバルタブバーで扱える
- 左一覧から同じ分析結果を再度開いたとき、既存タブを再アクティブ化できる
- 分析結果タブの表示名に result.name を使う
- 分析結果タブはデータタブと同じ高さにそろえ、やや広めにし、長い名前は省略表示する
- 分析結果タブの閉じる操作と、左一覧からの削除操作を分離している
- 回帰分析、信頼区間、基本統計量の作成後に分析結果一覧を再取得する
- ワークスペース上部の データ / 分析結果 切替の高さを縮小している

### 一部実装済み

- 分析結果の専用プレビューは regression / confidence_interval / descriptive_statistics に対応済み
- statistical_test / did / rdd / heckman は一覧表示できるが、中央の専用プレビューは未対応

### 未実装

- name / description / summary_text を更新する UI と保存 API
- 分析結果メタデータのインライン編集または詳細編集ダイアログ
- 結果比較ビュー、ピン留め、アーカイブ、検索・フィルタ UI

## 非ゴール

- 本仕様では実装方法や Zustand ストア構成までは固定しない。
- 本仕様では結果比較ビューやピン留め機能は必須としない。
- 本仕様では分析結果の内容表示レイアウトの詳細までは扱わない。

## 1. 画面ワイヤーの文章仕様

### 1-1. 画面全体構成

実装状態: 実装済み

画面は 3 つの役割に分ける。

- 左ペイン: ワークスペースナビゲータ
- 中央メイン: 選択中コンテンツの表示領域
- 上部または中央内タブ: 現在開いているビューのみを保持する一時的な作業コンテキスト

左ペインは永続的な一覧、中央タブは一時表示とし、責務を分離する。

2026-04-29 時点では、中央タブはデータプレビューと分析結果プレビューを共通のワークスペースタブとして扱う。分析設定フォーム群はこの共通タブの外側に置く。

### 1-2. 左ペイン上部の切替

実装状態: 実装済み

左ペイン最上部に 2 セグメントの切替を置く。

- データ
- 分析結果

要件は次のとおり。

- 初期表示は データ
- 切替状態はセッション中は維持してよい
- 切替はクリック範囲を広くし、現在選択中が一目で分かる見た目にする
- キーボード操作で切替可能にする

追加 UI 方針:

- セグメントの高さは既存実装よりやや低くし、左ペイン上部の圧迫感を下げる

### 1-3. データ表示時

データ表示時は現行のテーブル一覧を維持する。

- 一覧項目クリックで DataPreview を開く
- 空状態ではデータ取込を促す案内文を表示する
- 現在アクティブなテーブルは強調表示する

### 1-4. 分析結果表示時

分析結果表示時は、左ペインに分析結果の一覧を表示する。

一覧の基本構造は次の順で整理する。

1. 分析種別ごとのグループ
2. 必要に応じて元テーブル名でまとまりを作る
3. 各結果を作成日時の新しい順に並べる

最初の段階では、次の 3 グループを表示対象とする。

- 基本統計量
- 信頼区間
- 回帰分析

将来的には同じ枠組みで次を追加できるようにする。

- 統計的検定
- DID
- RDD
- Heckman
- 相関行列

### 1-5. 分析結果項目クリック時の挙動

実装状態: 実装済み

分析結果項目をクリックしたときの要件は次のとおり。

- クリックすると該当の結果詳細を中央メイン領域で開く
- 結果を開く操作で、分析設定フォームには遷移しない
- 既に同じ結果が中央タブで開いている場合は、そのタブをアクティブ化する
- 未ロードの詳細は既存の結果詳細 API で取得する

### 1-6. タブと削除のルール

実装状態: 実装済み

タブと削除の責務を分離する。

- タブの閉じる操作: 表示中ビューだけを閉じる
- 左一覧の削除操作: サーバ上の分析結果を削除する

タブを閉じても分析結果一覧から再度開けることを必須要件とする。

補足:

- 現在の回帰分析画面・信頼区間画面内のローカル結果タブは既存実装として残るが、結果作成後の主導線は中央のグローバルタブへ戻す

### 1-7. 左一覧の行内アクション

各結果行には必要最小限の行内アクションを置く。

- 開く
- 出力
- 削除

初期実装では、誤操作を避けるために削除はケバブメニューまたは右端の明示ボタンとする。
削除は確認ダイアログを経由することを推奨する。

### 1-8. 空状態とロード状態

分析結果タブの空状態では次を表示する。

- まだ分析結果がない旨
- どの分析画面から結果が作成されるか
- 初学者向けに次の行動を 1 文で示す

ロード状態では一覧全体に対するスケルトンまたはプレースホルダを表示する。

### 1-9. 初学者向けの補助導線

ユーザーの使いやすさを優先し、結果行には次の補助情報を短く見せる。

- 何の分析か
- どのテーブルに対して実行したか
- いつ作ったか

必要ならホバーまたはサブテキストで次の情報を見せる。

- モデル種別
- 信頼水準
- 列数や変数数

## 2. 左一覧の 1 行データ項目仕様

### 2-1. 共通必須項目

左一覧の 1 行は少なくとも次の項目を保持する。

- resultId: 結果の一意 ID
- resultType: 分析種別
- resultTypeLabel: 画面表示用の分析種別ラベル
- resultName: 結果名
- tableName: 元テーブル名
- createdAt: 作成日時
- summaryText: 行の補助表示文

### 2-2. 表示仕様

実装状態: 一部実装済み

1 行の見た目は 3 層で構成する。

- 1 段目: 分析種別バッジ + 結果名
- 2 段目: 元テーブル名
- 3 段目: 作成日時または補助情報

長い名前は省略表示してよいが、ホバーまたはツールチップで全文確認できることが望ましい。

中央タブ側については次を追加要件とする。

- 分析結果タブのラベルには result.name を使う
- データタブと同じ高さにする
- データタブより少し広い最小幅を持たせる
- 長い name は 1 行省略表示し、必要に応じて title 属性などで全文参照可能にする

### 2-3. resultType ごとの summaryText

summaryText は resultType ごとに次のように使い分ける。

- descriptive_statistics: 対象列数、統計量数
- confidence_interval: 対象統計量、信頼水準
- regression: モデル種別、従属変数名
- statistical_test: 検定名
- did: 推定手法名または処置変数
- rdd: カットオフと推定方向
- heckman: 2 段階推定の有無またはモデル種別

summaryText は一覧の視認性を優先し、1 行で収まる長さにする。

### 2-4. 状態項目

将来拡張を見据えて、UI モデルとしては次の状態を持てる設計が望ましい。

- isOpen: 現在中央ビューで開いているか
- isActive: 現在アクティブ表示中か
- isPinned: ピン留めされているか
- isArchived: 通常一覧から隠すか

このうち初期必須は isOpen と isActive のみでよい。

### 2-5. 並び順

初期のデフォルト並び順は次のとおり。

1. 分析種別の表示順
2. 作成日時の降順

将来的には並び替え候補として次を許容する。

- 作成日時
- 名前
- 元テーブル名

### 2-6. フィルタ条件

中長期では次のフィルタが必要になる。

- 分析種別
- 元テーブル名
- キーワード検索

初期実装ではフィルタ UI を持たなくてもよいが、データモデルと API は追加しやすい形にしておく。

## 3. API レスポンス案

### 3-1. 必須方針

新規 API を増やすより、既存の一覧 API を拡張する方を優先する。

必須変更対象:

- GET /analysis/results のレスポンス拡張

既存 API のままで利用可能:

- GET /analysis/results/{result_id}
- DELETE /analysis/results/{result_id}
- POST /analysis/results/output

### 3-2. 一覧 API のレスポンス項目案

GET /analysis/results の各要素に次を追加する。

- id
- name
- description
- createdAt
- tableName
- resultType
- resultTypeLabel
- modelType
- summaryText

最低限、tableName と resultType は必須とする。これがないと一覧から結果を識別しづらい。

### 3-3. レスポンス例

```json
{
  "code": "OK",
  "result": {
    "results": [
      {
        "id": "result-reg-001",
        "name": "賃金回帰 1",
        "description": "対数賃金を年齢と学歴で回帰",
        "createdAt": "2026-04-29T10:15:30Z",
        "tableName": "賃金データ_加工後",
        "resultType": "regression",
        "resultTypeLabel": "回帰分析",
        "modelType": "ols",
        "summaryText": "OLS / 従属変数: log_wage"
      },
      {
        "id": "result-ci-001",
        "name": "平均年収の信頼区間",
        "description": "95% 信頼区間",
        "createdAt": "2026-04-29T10:20:10Z",
        "tableName": "賃金データ_加工後",
        "resultType": "confidence_interval",
        "resultTypeLabel": "信頼区間",
        "modelType": null,
        "summaryText": "mean / 95%"
      },
      {
        "id": "result-ds-001",
        "name": "基本統計量 1",
        "description": "主要列の要約統計",
        "createdAt": "2026-04-29T10:25:00Z",
        "tableName": "賃金データ_加工後",
        "resultType": "descriptive_statistics",
        "resultTypeLabel": "基本統計量",
        "modelType": null,
        "summaryText": "8 列 / 11 統計量"
      }
    ]
  }
}
```

### 3-4. スキーマ案

API モデル上のサマリーは次の形を推奨する。

```ts
type AnalysisResultSummary = {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  tableName: string;
  resultType:
    | "descriptive_statistics"
    | "confidence_interval"
    | "regression"
    | "statistical_test"
    | "did"
    | "rdd"
    | "heckman";
  resultTypeLabel: string;
  modelType: string | null;
  summaryText: string;
};
```

### 3-5. 推奨する将来拡張

件数増加に備え、将来的には GET /analysis/results に次のクエリ追加を推奨する。

- resultType
- tableName
- q
- sortBy
- order
- limit
- cursor

このクエリは初期実装では必須ではない。

### 3-6. 任意の新規 API 候補

初期実装に必須ではないが、長期的には次の API が有用である。

1. 結果のピン留め更新 API
2. 結果のアーカイブ更新 API
3. 最近開いた結果の記録 API またはローカル永続化

ただし、今回の UI 追加に対して必須なのは一覧 API の拡張だけである。

## 4. API 実装仕様

### 4-1. 実装スコープ

次フェーズの API 修正では、次だけを必須スコープとする。

- GET /api/analysis/results のレスポンス拡張
- 一覧サマリー生成ロジックの拡張
- OpenAPI 再生成に伴う app 側の型同期
- バックエンドテストの追加更新

次は今回の実装スコープ外とする。

- 新規エンドポイント追加
- クエリパラメータによる絞り込み
- ピン留め、アーカイブ、最近開いた結果の永続化
- GET /api/analysis/results/{result_id} のレスポンス変更

### 4-2. 互換性方針

今回の変更は非破壊的な拡張とする。

- GET /api/analysis/results は既存フィールドを残したまま項目追加のみ行う
- GET /api/analysis/results/{result_id} は変更しない
- DELETE /api/analysis/results/{result_id} は変更しない
- POST /api/analysis/results/output は変更しない

特に GET /api/analysis/results/{result_id} は、現在の SuccessResponse の直下に AnalysisResultDetail を返す形を維持する。詳細用の二重ラッパーモデルは追加しない。

### 4-3. 変更対象ファイル

API 側で変更対象になるファイルは次を想定する。

1. api/economicon/schemas/result_management.py
2. api/economicon/services/data/analysis_result.py
3. api/economicon/services/data/analysis_result_store.py
4. api/economicon/services/results/result.py
5. api/tests/regressions/test_analysis_result_store.py
6. api/tests/statistics/test_descriptive_statistics_result.py
7. api/tests/statistics/test_confidence_interval_result.py
8. api/tests/statistics/test_statistical_test_result.py
9. 必要なら回帰結果系テスト

ルーターの path や service interface は維持し、主に schema と summary 生成ロジックを更新する。

### 4-4. Pydantic スキーマ変更案

api/economicon/schemas/result_management.py の AnalysisResultSummary は次の項目を持つ。

```python
class AnalysisResultSummary(BaseResult):
  id: str
  name: str
  description: str
  created_at: str
  table_name: str
  result_type: str
  result_type_label: str
  model_type: str | None
  summary_text: str
```

JSON キーは既存方針どおり camelCase で公開する。

```json
{
  "id": "...",
  "name": "...",
  "description": "...",
  "createdAt": "...",
  "tableName": "...",
  "resultType": "...",
  "resultTypeLabel": "...",
  "modelType": "...",
  "summaryText": "..."
}
```

### 4-5. AnalysisResult モデル変更案

api/economicon/services/data/analysis_result.py では to_summary_dict を拡張する。

返却項目は次で固定する。

- id
- name
- description
- createdAt
- tableName
- resultType
- resultTypeLabel
- modelType
- summaryText

実装方式は次のいずれかでよい。

1. to_summary_dict の中で直接 summaryText を組み立てる
2. AnalysisResult に summary 用 helper を追加して分離する

可読性の観点では 2 を推奨する。推奨 helper は次のとおり。

- \_get_result_type_label()
- \_build_summary_text()

### 4-6. resultTypeLabel の変換仕様

resultTypeLabel は API で返す表示用ラベルであり、初期値は次で固定する。

- descriptive_statistics -> 基本統計量
- confidence_interval -> 信頼区間
- regression -> 回帰分析
- statistical_test -> 統計的検定
- did -> DID
- rdd -> RDD
- heckman -> Heckman

未知の resultType はそのまま返さず、フォールバックとして 分析結果 を返す。

### 4-7. summaryText の生成仕様

summaryText は resultData から決定的に生成する。UI 側で再組み立てしない。

#### descriptive_statistics

resultData の statistics を使って次の形式で返す。

- {列数} 列 / {統計量数} 統計量

列数は statistics のキー数とする。
統計量数は最初の列に含まれる統計量キー数を基本とする。

例:

- 8 列 / 11 統計量

#### confidence_interval

resultData の statistic.type と confidenceLevel を使って次の形式で返す。

- {statistic.type} / {confidenceLevelPercent}%

confidenceLevel は 0.95 のような値を 95% に変換する。
小数第 2 位までで十分だが、整数で表せる場合は整数表記を優先する。

例:

- mean / 95%
- variance / 90%

#### regression

modelType と resultData.dependentVariable を使って次の形式で返す。

- {modelTypeUpper} / 従属変数: {dependentVariable}

modelType が null の場合は 回帰分析 / 従属変数: {dependentVariable} とする。
dependentVariable が取得できない場合は modelTypeUpper のみ返す。

例:

- OLS / 従属変数: log_wage
- FE / 従属変数: y

#### statistical_test

resultData.testType があれば次の形式で返す。

- {testType}

resultData.testType が無い場合は 検定結果 を返す。

#### did

phase 1 では次の優先順で summaryText を組み立てる。

1. resultData.modelSummary.modelName
2. modelType
3. DID

#### rdd

phase 1 では次の優先順で summaryText を組み立てる。

1. resultData.specification.bandwidth と resultData.specification.cutoff を読める場合は bw={bandwidth} / cutoff={cutoff}
2. resultData.cutoff があれば cutoff={cutoff}
3. RDD

#### fallback

未対応の resultType、または必要なキーが無い場合の summaryText は次とする。

- description が空でなければ description
- それも空なら resultTypeLabel

summaryText は必ず非空文字列を返す。

### 4-8. 実装時の疑似コード

```python
def to_summary_dict(self) -> dict[str, Any]:
  return {
    "id": self._id,
    "name": self._name,
    "description": self._description,
    "createdAt": self._created_at,
    "tableName": self._table_name,
    "resultType": self._result_type,
    "resultTypeLabel": self._get_result_type_label(),
    "modelType": self._model_type,
    "summaryText": self._build_summary_text(),
  }
```

### 4-9. AnalysisResultStore の変更方針

api/economicon/services/data/analysis_result_store.py の public interface は変更しない。

- get_all_summaries() の戻り値の各 dict に追加項目が入るようにする
- メソッド名、引数、戻り値の外枠は維持する

get_all_summaries の docstring は新しいキー一覧に更新する。

### 4-10. サービス層の変更方針

api/economicon/services/results/result.py の GetAllAnalysisResults は実質変更不要とする。

理由:

- 現在すでに result_store.get_all_summaries() の戻り値をそのまま返しているため
- 今回の仕様差分は summary dict の中身だけで完結できるため

### 4-11. OpenAPI とフロント同期

API 修正後は必ず次を実行する。

1. app/pnpm gen:all
2. フロント側の generated model 更新確認
3. 一覧 UI で新フィールドを利用する実装へ接続

型再生成後、app/src/api/model/analysisResultSummary.ts に追加項目が出ることを確認する。

## 5. API テスト仕様

### 5-1. ストア単体テスト

api/tests/regressions/test_analysis_result_store.py に次を追加または更新する。

- get_all_summaries の各要素に tableName が含まれる
- get_all_summaries の各要素に resultType が含まれる
- get_all_summaries の各要素に resultTypeLabel が含まれる
- get_all_summaries の各要素に modelType が含まれる
- get_all_summaries の各要素に summaryText が含まれる
- summaryText が空文字でない

### 5-2. API ルーターテスト

api/tests/regressions/test_analysis_result_store.py の GET /api/analysis/results テストを拡張し、一覧要素の必須キーを確認する。

必須アサート:

- data["result"]["results"] が list
- 各要素に id, name, description, createdAt, tableName, resultType, resultTypeLabel, modelType, summaryText が存在

### 5-3. 分析種別ごとの結合テスト

既存の結果取得テストに加え、一覧 API でも最低限の種別確認を追加する。

- basic descriptive statistics 実行後に resultType == descriptive_statistics
- confidence interval 実行後に resultType == confidence_interval
- regression 実行後に resultType == regression

必要なら新規テストを追加するより、既存の POST -> GET 系テストに一覧取得を 1 ケースずつ足す方が保守しやすい。

### 5-4. 非回帰 result の modelType

回帰以外の resultType では modelType が null または仕様どおりの値で返ることを確認する。

少なくとも次を担保する。

- descriptive_statistics -> null
- confidence_interval -> null
- regression -> 非 null を許容

### 5-5. 既存詳細 API 非回帰テスト

GET /api/analysis/results/{result_id} の詳細 API はレスポンス形状を変えないため、既存テストは原則そのまま通ることを確認する。新規フィールド追加の影響で失敗しないことが回帰条件である。

## 6. 実装順序

次フェーズの API 実装は次の順で進める。

1. AnalysisResultSummary スキーマを拡張
2. AnalysisResult.to_summary_dict を拡張
3. ストア docstring とテストを更新
4. GET /api/analysis/results の API テストを更新
5. app/pnpm gen:all を実行
6. フロント側で生成型を確認

この順序なら、変更の責務が局所化され、詳細 API や他の分析サービスへの影響を最小化できる。

## 7. フロント実装方針

### 7-1. 中央領域のタブ管理

実装状態: 実装済み

中央領域はデータ専用タブと分析結果専用タブに分けず、共通のワークスペースタブストアで管理する。

タブモデルは少なくとも次を持つ。

- id
- kind: data | result
- title
- tableName または resultId
- result detail（result タブ時）

同一 resultId を再度開こうとした場合は新規タブを作らず、既存タブをアクティブ化する。

### 7-2. 新規分析結果作成後の同期

実装状態: 実装済み

回帰分析、信頼区間、基本統計量を実行して新しい結果が作成されたら、少なくとも次を行う。

- 成功後に一覧 API を再取得する
- 生成された resultId の詳細を取得できる場合は中央のワークスペースタブへ開く
- 左の分析結果一覧が stale なまま残らないようにする

## 8. 追加仕様: 結果メタデータ編集 UI

### 8-1. 目的

実装状態: 未実装

分析結果の一覧性を高めるため、ユーザーが次の 3 項目を後から編集できる UI を用意する。

- name
- description
- summary_text

### 8-2. 推奨 UI 案

初期案としては次のいずれかが適している。

1. 左一覧の行アクションから開く「結果情報を編集」ダイアログ
2. 中央結果プレビュー上部の情報カードにある「編集」ボタンから開くサイドシート

初期実装では 1 を推奨する。理由は次のとおり。

- 左一覧との責務が近い
- 編集対象がメタデータに限定される
- 結果本体レイアウトを汚さない

### 8-3. フォーム項目仕様

編集ダイアログには少なくとも次を置く。

- name: 必須、1 行入力
- description: 任意、複数行入力
- summary_text: 任意、1 行入力。未入力時は API 側生成値へフォールバック可

補助仕様:

- name はタブ名にも反映される
- description は一覧の補助テキストまたは詳細情報として使える
- summary_text は左一覧の 3 段目表示に使う

### 8-4. 保存仕様

この UI を本実装するには、分析結果メタデータ更新 API が別途必要である。

必要最小 API 例:

- PATCH /api/analysis/results/{result_id}

更新対象:

- name
- description
- summary_text

現時点では API 未実装のため、本項目は仕様のみとする。

## 受け入れ基準

- 左サイドメニューで データ と 分析結果 を切り替えられる。
- 分析結果一覧の 1 行だけで、何の結果か判断できる。
- 結果を開く操作でフォームには戻らず、結果表示へ直接遷移する。
- タブを閉じても結果は一覧から再オープンできる。
- 結果削除は明示操作でのみサーバ削除される。
- 新しい分析種別を追加しても、一覧 UI の大枠を変えずに拡張できる。
- API 側では GET /api/analysis/results のみの拡張で要件を満たせる。
- GET /api/analysis/results/{result_id} のレスポンス形状は維持される。

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

| 項目                                                                       | 状態         | 補足                                               |
| -------------------------------------------------------------------------- | ------------ | -------------------------------------------------- |
| 左サイドメニューで データ / 分析結果 を切り替える                          | 実装済み     | セグメント切替を実装済み                           |
| 中央領域で データタブ と 分析結果タブ を共通タブバーで扱う                 | 実装済み     | 同一 resultId の再アクティブ化を含む               |
| 分析結果タブ名に result.name を使う                                        | 実装済み     | 長い名前は省略表示                                 |
| 分析結果タブの閉じる操作と左一覧の削除操作を分離する                       | 実装済み     | タブ close はローカル、削除はサーバ反映            |
| 回帰分析・信頼区間・基本統計量の作成後に左一覧を更新する                   | 実装済み     | 作成成功後に一覧 API を再取得                      |
| ワークスペース上部の データ / 分析結果 切替の高さを縮小する                | 実装済み     | 左ペイン上部の圧迫感を軽減                         |
| regression / confidence_interval / descriptive_statistics の専用プレビュー | 一部実装済み | この 3 種別のみ中央専用プレビュー対応              |
| statistical_test / did / rdd / heckman の中央専用プレビュー                | 未実装       | 一覧表示は可能だが詳細描画は未対応                 |
| 分析結果メタデータ編集 UI                                                  | 未実装       | name / description / summary の編集導線は未着手    |
| 分析結果メタデータ更新 API                                                 | 実装済み     | PATCH /api/analysis/results/{result_id} を追加済み |
| 結果比較、ピン留め、アーカイブ、検索・フィルタ                             | 未実装       | 中長期の拡張対象                                   |
| データプレビュー以外のフォーム系機能のワークスペースタブ化                 | 未実装       | 本仕様で方針のみ定義する                           |
| MainView とタブの密度最適化                                                | 未実装       | Compact 指向の具体ルールを本仕様に追記             |

## 非ゴール

- 本仕様では実装方法や Zustand ストア構成までは固定しない。
- 本仕様では結果比較ビューやピン留め機能は必須としない。
- 本仕様では分析結果の内容表示レイアウトの詳細までは扱わない。

## 1. 画面ワイヤーの文章仕様

### 1-1. 画面全体構成

画面は 3 つの役割に分ける。

- 左ペイン: ワークスペースナビゲータ
- 中央メイン: 選択中コンテンツの表示領域
- 上部または中央内タブ: 現在開いているビューのみを保持する一時的な作業コンテキスト

左ペインは永続的な一覧、中央タブは一時表示とし、責務を分離する。

2026-04-29 時点では、中央タブはデータプレビューと分析結果プレビューを共通のワークスペースタブとして扱う。分析設定フォーム群はこの共通タブの外側に置く。

### 1-2. 左ペイン上部の切替

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

分析結果項目をクリックしたときの要件は次のとおり。

- クリックすると該当の結果詳細を中央メイン領域で開く
- 結果を開く操作で、分析設定フォームには遷移しない
- 既に同じ結果が中央タブで開いている場合は、そのタブをアクティブ化する
- 未ロードの詳細は既存の結果詳細 API で取得する

### 1-6. タブと削除のルール

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

### 3-1a. 必要 API 一覧

今回の仕様を満たすために必要な API は次のとおり。

| API                                      | 用途                                       | 新規/既存 | 必須度 |
| ---------------------------------------- | ------------------------------------------ | --------- | ------ |
| GET /api/analysis/results                | 左一覧の表示、一覧再取得                   | 既存拡張  | 必須   |
| GET /api/analysis/results/{result_id}    | 結果詳細表示、編集後の詳細同期             | 既存流用  | 必須   |
| PATCH /api/analysis/results/{result_id}  | name / description / summary_text 編集保存 | 新規      | 必須   |
| DELETE /api/analysis/results/{result_id} | 左一覧からの削除                           | 既存流用  | 必須   |
| POST /api/analysis/results/output        | 出力ダイアログからの結果出力               | 既存流用  | 必須   |

このうち新規追加が必要なのは PATCH /api/analysis/results/{result_id} のみである。

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

分析結果ナビゲーション自体に対して必須なのは一覧 API の拡張である。
ただし、name / description / summary_text 編集を含める場合は PATCH /api/analysis/results/{result_id} も必須となる。

### 3-7. メタデータ更新 API 案

分析結果メタデータ編集を実装する場合は、一覧 API の拡張とは別に更新 API を追加する。

推奨 API:

- PATCH /api/analysis/results/{result_id}

リクエスト項目は次を推奨する。

- name
- description
- summaryTextOverride

summaryTextOverride は、UI 上の summary_text 編集値を保存するための上書き専用フィールドとする。
summaryText そのものを保存項目名にしない理由は、summaryText が本来 API 自動生成値でもあり得るためである。

レスポンスは少なくとも次を返す。

- updatedSummary: 最新の AnalysisResultSummary
- updatedDetail: 可能なら最新の AnalysisResultDetail

この形で返す理由は、左一覧、中央タブ名、詳細ヘッダを 1 回の保存応答で同期できるためである。

リクエスト例:

```json
{
  "name": "賃金回帰 2",
  "description": "説明変数を追加した再推定",
  "summaryTextOverride": "OLS / 従属変数: log_wage / controls added"
}
```

レスポンス例:

```json
{
  "code": "OK",
  "result": {
    "updatedSummary": {
      "id": "result-reg-001",
      "name": "賃金回帰 2",
      "description": "説明変数を追加した再推定",
      "createdAt": "2026-04-29T10:15:30Z",
      "tableName": "賃金データ_加工後",
      "resultType": "regression",
      "resultTypeLabel": "回帰分析",
      "modelType": "ols",
      "summaryText": "OLS / 従属変数: log_wage / controls added"
    },
    "updatedDetail": {
      "id": "result-reg-001"
    }
  }
}
```

### 3-8. 更新 API のエラー方針

PATCH /api/analysis/results/{result_id} は既存 API と同じ SuccessResponse / ErrorResponse の枠組みに揃える。

想定エラー:

- RESULT_NOT_FOUND: 指定 result_id が存在しない
- INVALID_INPUT: name が空、長さ超過、全項目未指定など
- RESULT_UPDATE_FAILED: 永続化失敗または不整合

message と details は既存 API と同様に完全一致アサート可能な安定文言とする。

### 3-9. 更新 API と既存 API の責務分担

API ごとの責務は次のように分ける。

- GET /api/analysis/results: 一覧表示に必要な最小情報を返す
- GET /api/analysis/results/{result_id}: 詳細表示に必要な完全情報を返す
- PATCH /api/analysis/results/{result_id}: メタデータだけを更新し、最新の一覧・詳細同期に必要な情報を返す
- DELETE /api/analysis/results/{result_id}: 結果削除のみを担当する
- POST /api/analysis/results/output: 出力のみを担当する

PATCH API は resultData 本体を更新しない。対象は name / description / summaryTextOverride のみとする。

## 4. API 実装仕様

### 4-1. 実装スコープ

次フェーズの API 修正では、次だけを必須スコープとする。

- GET /api/analysis/results のレスポンス拡張
- 一覧サマリー生成ロジックの拡張
- OpenAPI 再生成に伴う app 側の型同期
- バックエンドテストの追加更新
- 分析結果メタデータ更新 API の追加

次は今回の実装スコープ外とする。

- 新規エンドポイント追加
- クエリパラメータによる絞り込み
- ピン留め、アーカイブ、最近開いた結果の永続化
- GET /api/analysis/results/{result_id} のレスポンス変更

ただし、PATCH /api/analysis/results/{result_id} は今回のメタデータ編集要件のために追加対象へ含める。

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
10. api/economicon/routers/result_management.py
11. 必要なら更新用 schema を定義するファイル

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

PATCH 用には少なくとも次の schema を追加する。

```python
class UpdateAnalysisResultRequest(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=100)
  description: str | None = Field(default=None, max_length=1000)
  summary_text_override: str | None = Field(default=None, max_length=200)


class UpdateAnalysisResultResult(BaseModel):
  updated_summary: AnalysisResultSummary
  updated_detail: AnalysisResultDetail | None = None
```

公開 JSON は camelCase とする。

```json
{
  "name": "...",
  "description": "...",
  "summaryTextOverride": "..."
}
```

summaryTextOverride は未指定と null と空文字を区別して扱う。

- 未指定: 当該項目を変更しない
- null: 自動生成へ戻す
- 空文字: サーバ側で null に正規化する

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

PATCH API に対応するため、ストアまたは永続化層には次の責務が追加で必要となる。

- 既存 result_id の検索
- name の更新
- description の更新
- summary_text_override の更新
- 更新後エンティティの再読込

推奨インターフェース例:

```python
def update_metadata(
  self,
  result_id: str,
  *,
  name: str | None = None,
  description: str | None = None,
  summary_text_override: str | None | UnsetType = UNSET,
) -> AnalysisResult:
  ...
```

summary_text_override は未指定と null を分けて扱う必要があるため、単純な Optional[str] だけではなく unset を表現できる形が望ましい。

### 4-10. サービス層の変更方針

api/economicon/services/results/result.py の GetAllAnalysisResults は実質変更不要とする。

理由:

- 現在すでに result_store.get_all_summaries() の戻り値をそのまま返しているため
- 今回の仕様差分は summary dict の中身だけで完結できるため

更新 API 用には、既存サービスと並列で次のユースケースを追加する。

- UpdateAnalysisResultMetadata

責務は次のとおり。

1. result_id の存在確認
2. request の項目正規化
3. 永続化層への更新委譲
4. 更新後の summary / detail 生成
5. SuccessResponse への整形

このユースケースでは resultData 本体には触れない。

### 4-11. OpenAPI とフロント同期

API 修正後は必ず次を実行する。

1. app/pnpm gen:all
2. フロント側の generated model 更新確認
3. 一覧 UI で新フィールドを利用する実装へ接続

型再生成後、app/src/api/model/analysisResultSummary.ts に追加項目が出ることを確認する。

### 4-12. summaryTextOverride の優先順位

summaryText の表示値は次の優先順位で決定する。

1. summaryTextOverride が non-null かつ非空文字列なら、その値を表示に使う
2. summaryTextOverride が null の場合は、既存ロジックで自動生成した summaryText を使う

空文字列は保存時に null と同義に正規化し、自動生成へ戻す。

これにより、ユーザー編集値と API 自動生成値の責務を明確に分離する。

### 4-14. ルーター実装案

ルーターには次の path operation を追加する。

```python
@router.patch("/results/{result_id}")
def update_analysis_result(
  result_id: str,
  request: UpdateAnalysisResultRequest,
) -> SuccessResponse[UpdateAnalysisResultResult]:
  ...
```

ルーターは次だけを担当する。

- Pydantic request の受理
- UseCase 呼び出し
- SuccessResponse / ErrorResponse の返却

入力値の意味づけや正規化は、ルーターではなく use case 側で行う。

### 4-15. バリデーション方針

サーバ側バリデーションは次を必須とする。

- name は空白のみ不可
- name の最大長を制限する
- description の最大長を制限する
- summaryTextOverride の最大長を制限する
- 3 項目すべて未指定の PATCH は INVALID_INPUT とする

name のトリム後空文字はエラーにする。
description と summaryTextOverride はトリム後空文字を null に正規化してよい。

### 4-16. 永続化モデル変更案

永続化される分析結果メタデータには次の保存項目が必要となる。

- name
- description
- summary_text_override

既存の AnalysisResult シリアライズ形式に summary_text_override が無い場合は、後方互換のため default null として読み込めるようにする。

保存データ例:

```json
{
  "id": "result-reg-001",
  "name": "賃金回帰 2",
  "description": "説明変数を追加した再推定",
  "summary_text_override": "OLS / 従属変数: log_wage / controls added"
}
```

### 4-17. AnalysisResult ドメインモデル変更案

AnalysisResult ドメインモデルには次の属性または同等概念を追加する。

- summary_text_override

合わせて次の helper を持たせることを推奨する。

- with_updated_metadata(...)
- get_effective_summary_text()

get_effective_summary_text() は summaryTextOverride と自動生成 summaryText の優先順位を隠蔽する。

### 4-18. i18n 方針

更新 API の message は API 側の既存 i18n 方針に従う。

例:

- 結果が見つかりません
- 更新内容が空です
- 結果メタデータの更新に失敗しました

ユーザー向け文字列は \_() でラップし、テストでは完全一致で確認する。

### 4-19. フロント同期を見据えたレスポンス方針

PATCH のレスポンスで updatedSummary と updatedDetail を返す理由は次のとおり。

- 左一覧は updatedSummary だけで即座に更新できる
- 開いているタブのタイトルは updatedDetail.name で更新できる
- activeResultDetail を更新しても再フェッチ不要である

もし updatedDetail を返さない設計にする場合は、PATCH 成功後に GET /api/analysis/results/{result_id} を追加で叩く必要があるため、初期実装では返す方を推奨する。

### 4-13. 更新 API の互換性方針

PATCH /api/analysis/results/{result_id} の追加は既存 API を壊さない拡張とする。

- GET /api/analysis/results のレスポンス形式は維持する
- GET /api/analysis/results/{result_id} のレスポンス形式は維持する
- 既存クライアントは PATCH API を呼ばない限り影響を受けない

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

### 5-6. メタデータ更新 API テスト

PATCH /api/analysis/results/{result_id} に対して次を確認する。

- name 更新で updatedSummary.name が更新される
- description 更新で updatedSummary.description が更新される
- summaryTextOverride 更新で updatedSummary.summaryText が上書き値になる
- summaryTextOverride に空文字を送ると自動生成 summaryText に戻る
- 保存後、GET /api/analysis/results と GET /api/analysis/results/{result_id} の整合が崩れない
- 3 項目すべて未指定で PATCH すると INVALID_INPUT になる
- name が空白のみの場合に INVALID_INPUT になる
- 旧データに summary_text_override が無くても更新できる

## 6. 実装状況

実装済みの詳細設計はコードを正とし、この節以降には今後の判断に必要な要点だけを残す。

### 6-1. 実装済み

- 分析結果一覧のための API 拡張と PATCH /api/analysis/results/{result_id} は実装済み。
- 左ペインの分析結果一覧、result tab の再利用、分析後の一覧再取得は実装済み。
- ワークスペースタブストアは data tab / result tab / work tab の型を持つ。
- result tab 上の編集ボタンと EditAnalysisResultDialog は実装済み。
- 保存後の summary 更新、result tab タイトル更新、activeResultDetail 更新は実装済み。
- Table 相当コンポーネントは、実態として data / result / work を描画するワークスペース面になっている。

### 6-2. 命名整理案

現状の app/src/components/pages/Table.tsx と app/src/components/pages/Table.test.tsx は、実際の責務と名前が一致していない。

推奨案:

- ファイル名: app/src/components/pages/WorkspaceSurface.tsx
- コンポーネント名: WorkspaceSurface
- テストファイル名: app/src/components/pages/WorkspaceSurface.test.tsx

理由:

- Table は実テーブル描画ではなく、ワークスペース全体のタブ面を表している。
- VirtualTable という本来のテーブル描画コンポーネントが別に存在するため、意味衝突を避けられる。
- MainView 配下での役割は「ワークスペースの本文面」であり、Surface が最も責務に近い。

代替案:

- WorkspaceTabsView: タブ面であることは明確だが、本文描画の責務がやや弱く見える。
- WorkspaceView: MainView との責務境界が曖昧になりやすい。

現時点の推奨は WorkspaceSurface とする。

### 6-3. 関連して見直す名前

- MainView 内の DataPreview / AnalysisResultPreview は、長期的にはどちらも WorkspaceSurface を表示する入口として整理できる。
- Table.test.tsx の describe 名も WorkspaceSurface に合わせて更新するのが自然である。

## 7. 未実装項目

### 7-1. work tab の導線接続

work tab の型と描画先はあるが、実際に openWorkTab を叩く UI 導線は未実装である。

対象:

- JoinTable
- UnionTable
- CreateSimulationDataTable
- CalculationView
- ConfidenceIntervalView
- LinearRegressionForm

必要作業:

- 左ナビまたは各起点ボタンから openWorkTab を呼ぶ
- MainView のページ切替と work tab 起動ポリシーを統一する

### 7-2. work tab の状態モデル

現状の work tab は title / featureKey / dirty の最小情報のみで、作業セッションとしては未完成である。

未実装:

- draftValues 保持
- createdAt 保持
- dirty=true 時の close 確認ダイアログ
- reopen 時のセッション再利用ルール

### 7-3. 結果メタデータ編集の残件

初期導線は実装済みだが、次は未実装である。

- 左一覧の行アクションから編集ダイアログを開くショートカット導線
- 編集ダイアログを未保存変更ありで閉じるときの破棄確認

補足:

- 現在のフロントは summary_text 上書き値そのものを保持しておらず、入力欄は空文字初期値 + 現在 summaryText の placeholder 表示で運用している。

### 7-4. タブ UI の仕上げ

未実装:

- data / result / work の視覚的区別用アイコンまたはバッジ
- work tab を含む close ルールの明示的 UX 整備
- MainView 側の余白最適化の最終調整

### 7-5. phase 2 候補

次は work tab 化の対象候補として残す。

- DescriptiveStatistics
- CorrelationMatrix

## 8. 現在の判断メモ

- 実テーブル描画は VirtualTable が担当し、ワークスペース切替面は別名に分離する。
- 実装済み仕様の詳細はコードを正とし、この文書は残タスクと命名判断の記録に寄せる。
- 次の実装優先度は、work tab 導線接続、dirty 管理、左一覧からの編集導線の順とする。

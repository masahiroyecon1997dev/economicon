# API テスト修正・拡充方針

## 目的

- 現在失敗している API テストを再現し、原因を実装差分・gold 差分・期待値誤りに分解して修正する。
- 数値比較の許容誤差を 1e-8 基準で整理する。
- 既存の合成データ中心テストに加えて、test/data/parquet の実データを使う検証を追加する。

## 進捗状況

### 完了済み

- DID 用 synthetic data generator を追加し、生成入口を test/scripts/generate_synthetic_data.py に統合した。
- DID 用 Python benchmark を追加し、test/scripts/python/generate_benchmarks.py から synthetic_did_gold.json を生成できるようにした。
- api/tests/test_did.py を inline 生成から test/data 配下の生成済み fixture 読み込み方式に移行した。
- api/tests/rdd/conftest.py を runtime 生成から test/data/parquet/synthetic_rdd.parquet 読み込み方式に移行した。
- RDD benchmark 条件を API の既定値に合わせ、test/scripts/python/benchmarks/rdd.py の vce 設定と gold を更新した。
- api/tests/regressions/test_add_diagnostic_columns.py の診断列名期待値と Tobit 説明変数指定を修正した。
- 対象修正後の確認として、api/tests/test_did.py・api/tests/rdd/・api/tests/regressions/test_add_diagnostic_columns.py を再実行し、74 passed を確認した。
- test/data/parquet/plm_grunfeld.parquet を実データ fixture として追加し、同じ生成元から CSV fallback も出力する構成にした。
- test/scripts/python/generate_real_benchmarks.py を追加し、実データ parquet から Python gold を生成できるようにした。
- test/scripts/r/generate_r_benchmark.R を実データ parquet 起点へ更新し、arrow 非導入環境では同一生成元の CSV fallback を使うようにした。
- api/tests/integration_tests/test_grunfeld_consistency.py と api/tests/integration_tests/test_r_benchmark_external_validity.py を runtime 外部取得から parquet 読み込み方式へ移行した。
- Grunfeld 系 integration tests を再実行し、70 passed を確認した。

### 進行中

- 実データ parquet benchmark の生成手順を README または運用手順に反映する。

### 未着手

- 実データ parquet benchmark の生成手順を明文化し、pytest は生成済み JSON のみを参照する運用へ揃える。

## 現状の棚卸し

対象として挙がっていた DID, WLS, GLS, FGLS, PanelIV, RDD, Heckman, 信頼区間, 検定, 記述統計は、少なくとも以下の API テストファイルが既に存在する。

- api/tests/test_did.py
- api/tests/regressions/test_wls.py
- api/tests/regressions/test_gls.py
- api/tests/regressions/test_fgls.py
- api/tests/regressions/test_panel_iv.py
- api/tests/rdd/test_rdd.py
- api/tests/selection_models/heckman/test_heckman.py
- api/tests/statistics/test_confidence_interval.py
- api/tests/statistics/test_statistical_test.py
- api/tests/statistics/test_descriptive_statistics.py

不足の中心は、ファイル有無ではなく以下の 3 点。

- 失敗中テストの修正と、その原因の類型化
- 許容誤差ポリシーの統一
- 実データ parquet を使った外部妥当性テストの追加

## 許容誤差ポリシー

- 基本方針: 推定値・統計量・信頼区間の絶対許容差は 1e-8 を下限基準とする。
- 1e-8 より厳しい比較は基準逸脱として 1e-8 に統一する。
- 1e-8 より緩い比較は例外扱いとし、理由を個別に再検証する。
- `message` と `details` は数値許容差ではなく完全一致で検証する。

## 1e-8 より緩い箇所の一覧

以下は 1e-8 より緩い許容差を使っている箇所。現時点では列挙のみで、妥当性は次段階で個別判断する。

| ファイル                                                          | 現在値                      | 用途 / 備考                               |
| ----------------------------------------------------------------- | --------------------------- | ----------------------------------------- |
| api/tests/columns/test_calculate_column.py                        | 1e-5                        | 列計算の浮動小数比較                      |
| api/tests/columns/test_transform_column.py                        | 1e-5                        | 列変換の浮動小数比較                      |
| api/tests/regressions/test_ols.py                                 | 5e-3                        | HAC 比較                                  |
| api/tests/regressions/test_lasso.py                               | 1e-4                        | Lasso の gold 比較                        |
| api/tests/regressions/test_random_effects.py                      | 1e-3                        | RE gold 比較                              |
| api/tests/regressions/test_ridge.py                               | 1e-4, 0.05                  | Ridge / OLS 近接比較                      |
| api/tests/rdd/test_rdd.py                                         | 1e-6, 1e-4                  | bandwidth, placebo, rdrobust 比較         |
| api/tests/integration_tests/test_grunfeld_consistency.py          | 1e-6, 2e-3                  | HAC, 正則化比較                           |
| api/tests/integration_tests/test_r_benchmark_external_validity.py | 1e-5, 5e-3, 1e-2, 0.1, 2e-3 | GLM, R², IV 診断, IV/Probit/RE 相対許容差 |

補足:

- api/tests/regressions/test_lasso.py は docstring に `atol=1e-8` とある一方で、実際の定数は 1e-4 で不整合がある。
- api/tests/integration_tests/test_r_benchmark_external_validity.py には定数以外にも `atol=1e-4` の直書きがある。

## 1e-8 より厳しい箇所

以下は今回 1e-8 に統一する対象。

| ファイル                                                          | 旧値  | 新値 |
| ----------------------------------------------------------------- | ----- | ---- |
| api/tests/regressions/test_ols.py                                 | 1e-12 | 1e-8 |
| api/tests/regressions/test_iv.py                                  | 1e-12 | 1e-8 |
| api/tests/regressions/test_gls.py                                 | 1e-12 | 1e-8 |
| api/tests/regressions/test_fgls.py                                | 1e-10 | 1e-8 |
| api/tests/regressions/test_fixed_effects.py                       | 1e-12 | 1e-8 |
| api/tests/regressions/test_random_effects.py                      | 1e-12 | 1e-8 |
| api/tests/regressions/test_wls.py                                 | 1e-12 | 1e-8 |
| api/tests/statistics/test_create_correlation_table.py             | 1e-12 | 1e-8 |
| api/tests/integration_tests/test_grunfeld_consistency.py          | 1e-10 | 1e-8 |
| api/tests/integration_tests/test_r_benchmark_external_validity.py | 1e-10 | 1e-8 |

## failing test 修正の進め方

1. pytest 失敗一覧を取得する。
2. 各失敗を次のどれかに分類する。
   - API 実装が壊れている
   - 期待値または gold が古い
   - 許容差が不適切
   - エラーメッセージ完全一致が崩れている
3. まず既存合成データの失敗を直す。
4. 次に parquet 実データを使った追加テストを入れる。
5. 最後に R / Python 参照実装との再比較を行う。

## 追加テスト方針

### DID / RDD のテストデータ移行方針

#### 基本方針

- DID と RDD は、テスト実行時に `api/tests` 内で都度 `DataFrame` を組み立てる方式をやめる。
- 正常系の主要 fixture は `test/data` 配下の生成済み CSV / Parquet を唯一の入力ソースにする。
- 入力データの生成ロジックは `test/scripts/data_generators` に寄せ、生成入口は既存の `test/scripts/generate_synthetic_data.py` に統合する。
- benchmark は `test/benchmarks/python/synthetic` と `test/benchmarks/r/synthetic` に保存し、pytest は benchmark を再計算せず生成済み成果物を読む。
- pytest 側は「データ生成コードの正しさ」ではなく「生成済み fixture に対する API の振る舞い」を検証する構成にする。

#### RDD

現状:

- データ生成関数は `test/scripts/data_generators/rdd.py` に既に存在する。
- benchmark も `test/benchmarks/python/synthetic/synthetic_rdd_gold.json` と `test/benchmarks/r/synthetic/r_synthetic_rdd_gold.json` が存在する。
- しかし pytest は `api/tests/rdd/conftest.py` で乱数から再生成した `DataFrame` を直接 `TablesStore` に入れており、`test/data` の生成済み fixture を読んでいない。

対応方針:

1. `test/scripts/generate_synthetic_data.py` の RDD 出力を source of truth にする。
2. pytest の fixture は `test/data/csv/synthetic_rdd.csv` または `test/data/parquet/synthetic_rdd.parquet` を読み込んで `TablesStore` に登録する。
3. `TABLE_NO_LEFT`, `TABLE_STRING` のような異常系派生テーブルも、可能なら generator 側で派生 fixture を出力する。
4. payload の既定列名は生成済みデータの列名に揃える。現状の `runningVariable='running_var'` と runtime fixture の `x` の不整合はここで解消する。
5. benchmark 再生成手順を明文化し、Python / R の両 benchmark が fixture と同じデータを参照するよう統一する。

#### DID

現状:

- pytest は `api/tests/test_did.py` 内で inline に panel データを組み立てている。
- `test/scripts/data_generators` に DID 用 generator がまだ無い。
- DID 用 benchmark も既存の synthetic benchmark 群に含まれていない。

対応方針:

1. `test/scripts/data_generators/did.py` を新設し、正常系・重複 entity-time・非 binary treatment などの派生データを生成する。
2. `test/scripts/generate_synthetic_data.py` に DID を組み込み、少なくとも以下を `test/data` に出力する。
   - `synthetic_did`
   - `synthetic_did_duplicate`
   - `synthetic_did_bad_treatment`
3. Python benchmark を `test/benchmarks/python/synthetic`、必要なら R benchmark を `test/benchmarks/r/synthetic` に追加する。
4. pytest 側は inline 生成をやめ、生成済み fixture を読み込むだけにする。
5. 正常系 fixture は current implementation で absorbed されない説明変数を使う。現行の `x1 = entity_id + time_id` のような fully absorbed な構成は generator 側で排除する。

#### benchmark 生成の運用方針

- synthetic データを更新したら benchmark も同じ commit で更新する。
- benchmark の生成スクリプトは `test/scripts/python` / `test/scripts/r` に集約する。
- pytest から benchmark 生成を暗黙実行しない。未生成なら明示的に失敗または skip する。
- fixture 名、benchmark 名、pytest 参照名は `synthetic_<api>...` で統一する。

## この方式に未移行の API

ここでいう「未移行」は、主要な正常系 fixture / benchmark が `test/data` と `test/scripts/data_generators` を source of truth にせず、pytest 実行時の inline 生成または外部データ取得に依存している状態を指す。小さな異常系専用の一時 `DataFrame` は対象外とする。

### 1. DID API

- エンドポイント: `/api/analysis/did`
- 現状: generator・fixture・Python benchmark を追加し、pytest は生成済み fixture を読む構成に更新済み。
- 状態: 移行済み

### 2. RDD API

- エンドポイント: `/api/analysis/rdd`
- 現状: generator / benchmark / pytest fixture を生成済み fixture 読み込み方式に統一済み。
- 状態: 移行済み

### 3. Regression API の Grunfeld 統合系

- エンドポイント: `/api/analysis/regression`, `/api/analysis/results/{result_id}`
- 対象メソッド: OLS, FE, RE, IV, Logit, Probit, Lasso, Ridge
- 該当テスト: `api/tests/integration_tests/test_grunfeld_consistency.py`, `api/tests/integration_tests/test_r_benchmark_external_validity.py`
- 現状: `test/data/parquet/plm_grunfeld.parquet` を source of truth とし、Python / R benchmark をこの入力から生成する構成へ更新済み。
- 状態: 移行済み

補足:

- Heckman は `test/scripts/data_generators/heckman.py` と `test/data/csv/synthetic_heckman.csv` / `test/data/parquet/synthetic_heckman.parquet` を使う構成が既にあるため、この観点では移行済み。
- OLS / WLS / GLS / FGLS / IV / Tobit / Statistics も主要 fixture は `test/data` と synthetic benchmark を読む構成が既にある。

### 回帰系

| データ                                            | 主対象                         | 追加したい検証                               |
| ------------------------------------------------- | ------------------------------ | -------------------------------------------- |
| test/data/parquet/wooldridge_wage1.parquet        | OLS, log model                 | 係数, SE, R², 対数変換時の欠損・非正値エラー |
| test/data/parquet/wooldridge_hprice1.parquet      | OLS, GLS/WLS 比較候補          | スケーリング差のある説明変数での安定性       |
| test/data/parquet/wooldridge_vote1.parquet        | OLS, 記述統計                  | R², 相関, 基本統計量                         |
| test/data/parquet/aer_journals.parquet            | WLS, FGLS                      | 重み付け・不均一分散補正                     |
| test/data/parquet/aer_fatalities.parquet          | PanelIV, FE/RE, HAC            | entity/time 指定, 診断統計量                 |
| test/data/parquet/datasets_mtcars.parquet         | OLS, 信頼区間, 検定            | 純数値データでの係数・CI・t/F 検定           |
| test/data/parquet/palmerpenguins_penguins.parquet | 記述統計, 検定, Heckman 前処理 | 欠損値, ダミー変数, 文字列列除外             |

### DID / RDD / Heckman

- DID: 現実パネルデータで treatment と period の 2 値制約、重複 entity-time、イベントスタディ基準期間を追加確認する。
- RDD: 実データで cutoff 近傍観測不足、左右サンプル非対称、bin 生成の安定性を確認する。
- Heckman: 欠損発生メカニズムを含む実データ、または parquet 化した再現データで selection 方程式と outcome 方程式の両方を検証する。

## エラー系で追加する観点

- 分散ゼロ
- 完全多重共線性
- 自由度不足
- NaN / Inf 混入
- スペースのみ、日本語、絵文字、予約語を含むテーブル名・列名
- message / details の完全一致
- 同一リクエストの冪等性

## 実行順序

1. 失敗中 pytest の再現
2. 1e-8 より厳しい tolerance の統一
3. failing test の修正
4. 実データ parquet テストの追加
5. `api/.venv/Scripts/ruff check .`
6. 追加したテスト対象を中心に pytest 再実行

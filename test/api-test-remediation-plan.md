# API テスト修正・拡充方針

## 目的

- 現在失敗している API テストを再現し、原因を実装差分・gold 差分・期待値誤りに分解して修正する。
- 数値比較の許容誤差を 1e-8 基準で整理する。
- 既存の合成データ中心テストに加えて、test/data/parquet の実データを使う検証を追加する。

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

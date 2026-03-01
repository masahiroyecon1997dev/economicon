#!/usr/bin/env Rscript
# =============================================================================
# generate_r_benchmark.R
#
# Grunfeld データセットを用いた外的妥当性テスト用ベンチマークJSON生成。
#
# 出力:
#   tests/benchmarks/r_grunfeld_gold.json  (ワークスペースルートからの相対パス)
#   ※ Rscript を <workspace_root> から実行した場合。
#     RStudio から source() する場合も getwd() がワークスペースルートであれば同様。
#
# 収録モデル:
#   ols  - Pooled OLS (lm)
#   fe   - Fixed Effects / Within (plm, model = "within")
#   re   - Random Effects / Swamy-Arora (plm, model = "random")
#
# 精度:
#   jsonlite の digits = NA で IEEE 754 double の全桁を保持する。
#   これにより Python 側 (statsmodels / linearmodels) との比較で
#   atol=1e-8 (係数・SE)、atol=1e-5 (R²) の精度検証が可能。
#
# 変数名マッピング (API との対応):
#   R `(Intercept)` → JSON key `const`   (Python API は sm.add_constant で
#                                          列名 "const" を使用するため)
#   その他の変数名はそのまま使用する。
#
# 必要パッケージ:
#   install.packages(c("plm", "jsonlite"))
# =============================================================================

suppressPackageStartupMessages({
  library(plm)
  library(jsonlite)
})

# -----------------------------------------------------------------------------
# 0. 設定
# -----------------------------------------------------------------------------

# 出力先ディレクトリ（このスクリプトと同じ Rcode/ 配下）
SCRIPT_DIR  <- tryCatch(
  dirname(normalizePath(sys.frame(1)$ofile)),
  error = function(e) getwd()  # RStudio で source() した場合のフォールバック
)
TARGET_DIR  <- file.path(SCRIPT_DIR, "tests", "benchmarks")
OUTPUT_FILE <- file.path(TARGET_DIR, "r_grunfeld_gold.json")

# -----------------------------------------------------------------------------
# 1. データ読み込み
# -----------------------------------------------------------------------------

data("Grunfeld", package = "plm")

stopifnot(
  all(c("firm", "year", "inv", "value", "capital") %in% colnames(Grunfeld)),
  nrow(Grunfeld) == 200L   # 10 企業 × 20 年
)

# pdata.frame に変換（FE/RE 推定で使用）
pgrunfeld <- pdata.frame(Grunfeld, index = c("firm", "year"))

# -----------------------------------------------------------------------------
# 2. ヘルパー: 係数名の正規化
#    R の "(Intercept)" を Python API の "const" に統一する。
# -----------------------------------------------------------------------------
normalize_names <- function(named_vec) {
  names(named_vec) <- sub("^\\(Intercept\\)$", "const", names(named_vec))
  named_vec
}

# -----------------------------------------------------------------------------
# 3. OLS (Pooled OLS)
# -----------------------------------------------------------------------------
model_ols <- lm(inv ~ value + capital, data = Grunfeld)
s_ols     <- summary(model_ols)

coef_ols <- normalize_names(coef(model_ols))
se_ols   <- normalize_names(sqrt(diag(vcov(model_ols))))

# lm の R² は s_ols$r.squared; adjusted は s_ols$adj.r.squared
r2_ols     <- s_ols$r.squared
r2_adj_ols <- s_ols$adj.r.squared

ols_result <- list(
  coefficients = as.list(coef_ols),
  std_errors   = as.list(se_ols),
  r_squared    = r2_ols,
  adj_r_squared = r2_adj_ols
)

# -----------------------------------------------------------------------------
# 4. Fixed Effects (Within Estimator)
#    linearmodels.PanelOLS(entity_effects=True) と対応する。
#    R² は within R²（entity demeaning 後の残差二乗和ベース）。
# -----------------------------------------------------------------------------
model_fe <- plm(inv ~ value + capital,
                data  = pgrunfeld,
                model = "within")
s_fe     <- summary(model_fe)

coef_fe <- normalize_names(coef(model_fe))   # 定数項なし
se_fe   <- normalize_names(sqrt(diag(vcov(model_fe))))

# plm within モデルの r.squared:
#   s_fe$r.squared は名前付きベクトル。
#   [1] = "rsq"   (within R²)  ← linearmodels PanelOLS.rsquared と対応
#   [2] = "adjrsq" (adjusted within R²)
r2_within_fe     <- as.numeric(s_fe$r.squared["rsq"])
r2_adj_within_fe <- as.numeric(s_fe$r.squared["adjrsq"])

fe_result <- list(
  coefficients     = as.list(coef_fe),
  std_errors       = as.list(se_fe),
  r_squared_within = r2_within_fe,
  adj_r_squared_within = r2_adj_within_fe
)

# -----------------------------------------------------------------------------
# 5. Random Effects (Swamy-Arora)
#    linearmodels.RandomEffects と対応する。
#    R² は within R²（同上）および overall R²を両方記録する。
#    注意: RE の R² 定義は実装依存であるため atol=1e-5 で比較する。
# -----------------------------------------------------------------------------
model_re <- plm(inv ~ value + capital,
                data   = pgrunfeld,
                model  = "random",
                random.method = "swar")   # Swamy-Arora (plm デフォルト)
s_re     <- summary(model_re)

coef_re <- normalize_names(coef(model_re))  # const を含む
se_re   <- normalize_names(sqrt(diag(vcov(model_re))))

# plm random モデルの r.squared:
#   [1] = "rsq"   (within R²)
#   [2] = "adjrsq"
r2_within_re     <- as.numeric(s_re$r.squared["rsq"])
r2_adj_within_re <- as.numeric(s_re$r.squared["adjrsq"])

# overall R² は r.squared(model, type = "rss") で取得
r2_overall_re <- tryCatch(
  r.squared(model_re, type = "rss"),
  error = function(e) NA_real_
)

re_result <- list(
  coefficients         = as.list(coef_re),
  std_errors           = as.list(se_re),
  r_squared_within     = r2_within_re,
  adj_r_squared_within = r2_adj_within_re,
  r_squared_overall    = r2_overall_re
)

# -----------------------------------------------------------------------------
# 6. メタデータ
# -----------------------------------------------------------------------------
meta <- list(
  generated_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
  r_version    = as.character(getRversion()),
  plm_version  = as.character(packageVersion("plm")),
  dataset      = "Grunfeld (plm package)",
  n_obs        = nrow(Grunfeld),
  n_firms      = length(unique(Grunfeld$firm)),
  n_years      = length(unique(Grunfeld$year)),
  notes = paste(
    "係数・SE は atol=1e-8、R² は atol=1e-5 で statsmodels/linearmodels と比較予定。",
    "変数名: (Intercept) → const (Python API sm.add_constant の命名規則に合わせる)。",
    "FE/RE の r_squared_within は linearmodels の rsquared (within) と対応する。"
  )
)

# -----------------------------------------------------------------------------
# 7. 出力
# -----------------------------------------------------------------------------
benchmark_results <- list(
  meta = meta,
  ols  = ols_result,
  fe   = fe_result,
  re   = re_result
)

if (!dir.exists(TARGET_DIR)) {
  dir.create(TARGET_DIR, recursive = TRUE)
}

# digits = NA: IEEE 754 double の全桁を文字列変換なしで保持する
write_json(
  benchmark_results,
  OUTPUT_FILE,
  auto_unbox = TRUE,
  pretty     = TRUE,
  digits     = NA
)

cat(sprintf("Benchmark JSON written to: %s\n", OUTPUT_FILE))

# -----------------------------------------------------------------------------
# 8. 簡易サニティチェック（コンソール出力）
# -----------------------------------------------------------------------------
cat("\n=== OLS coefficients ===\n")
print(coef_ols)

cat("\n=== FE coefficients ===\n")
print(coef_fe)

cat("\n=== RE coefficients ===\n")
print(coef_re)

cat("\n=== R² summary ===\n")
cat(sprintf("  OLS  R²         : %.15f\n", r2_ols))
cat(sprintf("  FE   R²_within  : %.15f\n", r2_within_fe))
cat(sprintf("  RE   R²_within  : %.15f\n", r2_within_re))
if (!is.na(r2_overall_re)) {
  cat(sprintf("  RE   R²_overall : %.15f\n", r2_overall_re))
}

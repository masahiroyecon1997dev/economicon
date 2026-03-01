#!/usr/bin/env Rscript
# =============================================================================
# generate_r_benchmark.R
#
# Grunfeld データセットを用いた外的妥当性テスト用 Gold Standard JSON 生成。
# Python API (Economicon) の結果が R の参照実装と一致するかを検証するための
# ベンチマークデータを生成する。
#
# 出力:
#   tests/benchmarks/r_grunfeld_gold.json  (ワークスペースルートからの相対パス)
#   ※ Rscript を <workspace_root> から実行した場合。
#     RStudio から source() する場合も getwd() がワークスペースルートであれば同様。
#
# 収録モデル:
#   ols    - Pooled OLS (lm)                + 信頼区間 + F 検定
#   fe     - Fixed Effects / Within (plm)  + 信頼区間
#   re     - Random Effects / Swamy-Arora (plm)
#   logit  - Binary Logit (glm)            + Wald CI + LR 検定
#   probit - Binary Probit (glm)           + Wald CI + LR 検定
#   iv     - 2SLS (AER::ivreg)             + 信頼区間 + Wu-Hausman + Sargan
#   lasso  - Lasso 回帰 (glmnet)           + sklearn 互換の標準化係数
#   ridge  - Ridge 回帰 (glmnet)           + sklearn 互換の標準化係数
#
# 変数名マッピング (API との対応):
#   R `(Intercept)` → JSON key `const`   (Python API は sm.add_constant で
#                                          列名 "const" を使用するため)
#
# sklearn 互換の標準化:
#   sklearn の StandardScaler は population std (ddof=0) で除算する。
#   R の scale() は sample std (ddof=1) を使用するため、
#   明示的に population std で標準化して一致させる。
#
# 必要パッケージ:
#   install.packages(c("plm", "AER", "glmnet", "jsonlite"))
# =============================================================================

# =============================================================================
suppressPackageStartupMessages({
  for (pkg in c("plm", "AER", "glmnet", "jsonlite")) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      stop(sprintf(
        "Required package '%s' not found. Run: install.packages('%s')",
        pkg, pkg
      ))
    }
    library(pkg, character.only = TRUE)
  }
})

# -----------------------------------------------------------------------------
# 0. 設定・定数
# -----------------------------------------------------------------------------

LASSO_ALPHA <- 0.1   # sklearn: Lasso(alpha=0.1)
RIDGE_ALPHA <- 1.0   # sklearn: Ridge(alpha=1.0)

SCRIPT_DIR  <- tryCatch(
  dirname(normalizePath(sys.frame(1)$ofile)),
  error = function(e) getwd()
)
TARGET_DIR  <- file.path(SCRIPT_DIR, "tests", "benchmarks")
OUTPUT_FILE <- file.path(TARGET_DIR, "r_grunfeld_gold.json")

# -----------------------------------------------------------------------------
# 1. データ読み込みと前処理
# -----------------------------------------------------------------------------

data("Grunfeld", package = "plm")
stopifnot(
  all(c("firm", "year", "inv", "value", "capital") %in% colnames(Grunfeld)),
  nrow(Grunfeld) == 200L
)

N_OBS   <- nrow(Grunfeld)
N_FIRMS <- length(unique(Grunfeld$firm))
N_YEARS <- length(unique(Grunfeld$year))

pgrunfeld <- pdata.frame(Grunfeld, index = c("firm", "year"))

# 二値変数 (Logit/Probit 用)
# Python 側: (grunfeld["inv"] > grunfeld["inv"].median()).astype(float)
INV_MEDIAN       <- median(Grunfeld$inv)
Grunfeld$inv_high <- as.integer(Grunfeld$inv > INV_MEDIAN)
N_POSITIVE       <- sum(Grunfeld$inv_high)

# IV 用: 各 firm 内の value/capital の1期前ラグ (190 obs)
grunfeld_iv <- Grunfeld[order(Grunfeld$firm, Grunfeld$year), ]
grunfeld_iv$value_lag <- ave(
  grunfeld_iv$value, grunfeld_iv$firm,
  FUN = function(x) c(NA, head(x, -1))
)
grunfeld_iv$capital_lag <- ave(
  grunfeld_iv$capital, grunfeld_iv$firm,
  FUN = function(x) c(NA, head(x, -1))
)
grunfeld_iv <- na.omit(grunfeld_iv)
N_OBS_IV <- nrow(grunfeld_iv)  # 190

# Lasso/Ridge 用の設計行列
X_mat <- as.matrix(Grunfeld[, c("value", "capital")])
y_inv <- Grunfeld$inv

# sklearn の StandardScaler(ddof=0) と合わせるため population std で標準化
col_means  <- colMeans(X_mat)
col_sds_r  <- apply(X_mat, 2, sd)
col_sds_sk <- col_sds_r * sqrt((N_OBS - 1) / N_OBS)  # population std
X_std      <- scale(X_mat, center = col_means, scale = col_sds_sk)

# -----------------------------------------------------------------------------
# 2. ヘルパー関数
# -----------------------------------------------------------------------------

normalize_names <- function(named_vec) {
  names(named_vec) <- sub("^\\(Intercept\\)$", "const", names(named_vec))
  named_vec
}

coef_list <- function(m) as.list(normalize_names(coef(m)))
se_list   <- function(m) as.list(normalize_names(sqrt(diag(vcov(m)))))

rename_coef_keys <- function(keys) {
  sub("^\\(Intercept\\)$", "const", keys)
}

ci_list <- function(m, level = 0.95) {
  ci <- confint(m, level = level)
  result <- lapply(seq_len(nrow(ci)), function(i) {
    list(lower = ci[i, 1], upper = ci[i, 2])
  })
  names(result) <- rename_coef_keys(rownames(ci))
  result
}

# Wald CI (logit/probit 用 — profile CI は遅く Python の Wald CI と対応しない)
ci_wald_list <- function(m, level = 0.95) {
  ci <- confint.default(m, level = level)
  result <- lapply(seq_len(nrow(ci)), function(i) {
    list(lower = ci[i, 1], upper = ci[i, 2])
  })
  names(result) <- rename_coef_keys(rownames(ci))
  result
}

# -----------------------------------------------------------------------------
# 3. OLS (Pooled OLS) + 信頼区間 + F 検定
# -----------------------------------------------------------------------------
model_ols <- lm(inv ~ value + capital, data = Grunfeld)
s_ols     <- summary(model_ols)

ols_f <- list(
  statistic = as.numeric(s_ols$fstatistic["value"]),
  df1       = as.integer(s_ols$fstatistic["numdf"]),
  df2       = as.integer(s_ols$fstatistic["dendf"]),
  p_value   = as.numeric(pf(
    s_ols$fstatistic["value"],
    s_ols$fstatistic["numdf"],
    s_ols$fstatistic["dendf"],
    lower.tail = FALSE
  ))
)

ols_result <- list(
  coefficients  = coef_list(model_ols),
  std_errors    = se_list(model_ols),
  conf_int      = ci_list(model_ols),
  r_squared     = s_ols$r.squared,
  adj_r_squared = s_ols$adj.r.squared,
  f_test        = ols_f
)

# -----------------------------------------------------------------------------
# 4. Fixed Effects (Within) + 信頼区間
# -----------------------------------------------------------------------------
model_fe <- plm(inv ~ value + capital, data = pgrunfeld, model = "within")
s_fe     <- summary(model_fe)

fe_coef <- coef(model_fe)
fe_se   <- sqrt(diag(vcov(model_fe)))
fe_df   <- s_fe$df[2]
fe_crit <- qt(0.975, df = fe_df)
fe_ci_list <- lapply(seq_along(fe_coef), function(i) {
  list(lower = fe_coef[i] - fe_crit * fe_se[i],
       upper = fe_coef[i] + fe_crit * fe_se[i])
})
names(fe_ci_list) <- names(fe_coef)

fe_result <- list(
  coefficients         = coef_list(model_fe),
  std_errors           = se_list(model_fe),
  conf_int             = fe_ci_list,
  r_squared_within     = as.numeric(s_fe$r.squared["rsq"]),
  adj_r_squared_within = as.numeric(s_fe$r.squared["adjrsq"])
)

# -----------------------------------------------------------------------------
# 5. Random Effects (Swamy-Arora)
# -----------------------------------------------------------------------------
model_re <- plm(inv ~ value + capital,
                data = pgrunfeld, model = "random",
                random.method = "swar")
s_re <- summary(model_re)

re_result <- list(
  coefficients         = coef_list(model_re),
  std_errors           = se_list(model_re),
  r_squared_within     = as.numeric(s_re$r.squared["rsq"]),
  adj_r_squared_within = as.numeric(s_re$r.squared["adjrsq"])
)

# -----------------------------------------------------------------------------
# 6. Logit (inv_high ~ value + capital) + Wald CI + LR 検定
# -----------------------------------------------------------------------------
model_logit <- glm(
  inv_high ~ value + capital,
  data = Grunfeld, family = binomial(link = "logit")
)

logit_llf      <- as.numeric(logLik(model_logit))
logit_null_llf <- as.numeric(logLik(
  glm(inv_high ~ 1, data = Grunfeld, family = binomial(link = "logit"))
))
logit_lr_stat  <- model_logit$null.deviance - model_logit$deviance
logit_lr_df    <- as.integer(model_logit$df.null - model_logit$df.residual)

logit_result <- list(
  dep_var              = "inv_high",
  median_inv           = INV_MEDIAN,
  n_positive           = N_POSITIVE,
  coefficients         = coef_list(model_logit),
  std_errors           = se_list(model_logit),
  conf_int             = ci_wald_list(model_logit),
  pseudo_r_squared     = 1 - logit_llf / logit_null_llf,
  log_likelihood       = logit_llf,
  log_likelihood_null  = logit_null_llf,
  aic                  = AIC(model_logit),
  bic                  = BIC(model_logit),
  lr_test = list(
    statistic = logit_lr_stat,
    df        = logit_lr_df,
    p_value   = as.numeric(
      pchisq(logit_lr_stat, df = logit_lr_df, lower.tail = FALSE)
    )
  )
)

# -----------------------------------------------------------------------------
# 7. Probit (inv_high ~ value + capital) + Wald CI + LR 検定
# -----------------------------------------------------------------------------
model_probit <- glm(
  inv_high ~ value + capital,
  data = Grunfeld, family = binomial(link = "probit")
)

probit_llf      <- as.numeric(logLik(model_probit))
probit_null_llf <- as.numeric(logLik(
  glm(inv_high ~ 1, data = Grunfeld, family = binomial(link = "probit"))
))
probit_lr_stat  <- model_probit$null.deviance - model_probit$deviance
probit_lr_df    <- as.integer(model_probit$df.null - model_probit$df.residual)

probit_result <- list(
  dep_var              = "inv_high",
  coefficients         = coef_list(model_probit),
  std_errors           = se_list(model_probit),
  conf_int             = ci_wald_list(model_probit),
  pseudo_r_squared     = 1 - probit_llf / probit_null_llf,
  log_likelihood       = probit_llf,
  log_likelihood_null  = probit_null_llf,
  aic                  = AIC(model_probit),
  bic                  = BIC(model_probit),
  lr_test = list(
    statistic = probit_lr_stat,
    df        = probit_lr_df,
    p_value   = as.numeric(
      pchisq(probit_lr_stat, df = probit_lr_df, lower.tail = FALSE)
    )
  )
)

# -----------------------------------------------------------------------------
# 8. IV 2SLS (AER::ivreg) + 信頼区間 + Wu-Hausman + Sargan
#    API: dep=inv, exog=["value"], endog=["capital"],
#         instruments=["value_lag","capital_lag"]
#    ivreg: inv ~ value + capital | value + value_lag + capital_lag
# -----------------------------------------------------------------------------
model_iv  <- ivreg(
  inv ~ value + capital | value + value_lag + capital_lag,
  data = grunfeld_iv
)
s_iv_diag <- summary(model_iv, diagnostics = TRUE)
diag_m    <- s_iv_diag$diagnostics

iv_coef_v <- normalize_names(coef(model_iv))
iv_se_v   <- normalize_names(sqrt(diag(vcov(model_iv))))
iv_ci_raw <- confint(model_iv)
rownames(iv_ci_raw) <- rename_coef_keys(rownames(iv_ci_raw))
iv_ci_list <- lapply(seq_len(nrow(iv_ci_raw)), function(i) {
  list(lower = iv_ci_raw[i, 1], upper = iv_ci_raw[i, 2])
})
names(iv_ci_list) <- rownames(iv_ci_raw)

iv_rss <- sum(residuals(model_iv)^2)
iv_tss <- sum((grunfeld_iv$inv - mean(grunfeld_iv$inv))^2)

iv_result <- list(
  dep_var      = "inv",
  n_obs        = N_OBS_IV,
  coefficients = as.list(iv_coef_v),
  std_errors   = as.list(iv_se_v),
  conf_int     = iv_ci_list,
  r_squared    = 1 - iv_rss / iv_tss,
  wu_hausman = list(
    statistic = as.numeric(diag_m["Wu-Hausman", "statistic"]),
    df1       = as.integer(diag_m["Wu-Hausman", "df1"]),
    df2       = as.integer(diag_m["Wu-Hausman", "df2"]),
    p_value   = as.numeric(diag_m["Wu-Hausman", "p-value"])
  ),
  sargan = list(
    statistic = as.numeric(diag_m["Sargan", "statistic"]),
    df        = as.integer(diag_m["Sargan", "df1"]),
    p_value   = as.numeric(diag_m["Sargan", "p-value"])
  )
)

# -----------------------------------------------------------------------------
# 9. Lasso + sklearn 互換の標準化係数
#    sklearn: Pipeline([StandardScaler(ddof=0), Lasso(alpha=0.1)])
#    glmnet:  glmnet(X_std_pop, y, alpha=1, lambda=0.1, standardize=FALSE)
# -----------------------------------------------------------------------------
set.seed(42)
fit_lasso <- glmnet(
  X_std, y_inv,
  alpha = 1, lambda = LASSO_ALPHA,
  standardize = FALSE, intercept = TRUE
)
lasso_coef_mat    <- coef(fit_lasso)
lasso_coef_scaled <- as.numeric(lasso_coef_mat[c("value", "capital"), ])
names(lasso_coef_scaled) <- c("value", "capital")
lasso_coef_orig <- lasso_coef_scaled / col_sds_sk
names(lasso_coef_orig) <- c("value", "capital")
lasso_intercept_orig <- as.numeric(mean(y_inv) - sum(lasso_coef_orig * col_means))

lasso_result <- list(
  alpha       = LASSO_ALPHA,
  coef_scaled = as.list(lasso_coef_scaled),
  coef_orig   = as.list(c(const = lasso_intercept_orig, lasso_coef_orig)),
  notes       = paste(
    "coef_scaled は sklearn Pipeline(StandardScaler(ddof=0),",
    "Lasso(alpha=0.1)).coef_ (coefficientScaled) と対応する。"
  )
)

# -----------------------------------------------------------------------------
# 10. Ridge + sklearn 互換の標準化係数
#     sklearn: Pipeline([StandardScaler(ddof=0), Ridge(alpha=1.0)])
#     等価条件: glmnet lambda = sklearn_alpha / n
# -----------------------------------------------------------------------------
RIDGE_LAMBDA <- RIDGE_ALPHA / N_OBS

fit_ridge <- glmnet(
  X_std, y_inv,
  alpha = 0, lambda = RIDGE_LAMBDA,
  standardize = FALSE, intercept = TRUE
)
ridge_coef_mat    <- coef(fit_ridge)
ridge_coef_scaled <- as.numeric(ridge_coef_mat[c("value", "capital"), ])
names(ridge_coef_scaled) <- c("value", "capital")
ridge_coef_orig <- ridge_coef_scaled / col_sds_sk
names(ridge_coef_orig) <- c("value", "capital")
ridge_intercept_orig <- as.numeric(mean(y_inv) - sum(ridge_coef_orig * col_means))

ridge_result <- list(
  alpha        = RIDGE_ALPHA,
  glmnet_lambda = RIDGE_LAMBDA,
  coef_scaled  = as.list(ridge_coef_scaled),
  coef_orig    = as.list(c(const = ridge_intercept_orig, ridge_coef_orig)),
  notes        = sprintf(
    "coef_scaled は sklearn Pipeline(StandardScaler(ddof=0), Ridge(alpha=%.1f)).coef_ と対応。glmnet lambda = %.1f/%d = %.6f",
    RIDGE_ALPHA, RIDGE_ALPHA, N_OBS, RIDGE_LAMBDA
  )
)

# -----------------------------------------------------------------------------
# 11. メタデータ
# -----------------------------------------------------------------------------
meta <- list(
  generated_at   = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
  r_version      = as.character(getRversion()),
  plm_version    = as.character(packageVersion("plm")),
  aer_version    = as.character(packageVersion("AER")),
  glmnet_version = as.character(packageVersion("glmnet")),
  dataset        = "Grunfeld (plm package)",
  n_obs          = N_OBS,
  n_obs_iv       = N_OBS_IV,
  n_firms        = N_FIRMS,
  n_years        = N_YEARS,
  inv_median     = INV_MEDIAN,
  n_inv_high     = N_POSITIVE,
  tolerance_guide = list(
    ols_fe_re_coef      = "atol=1e-8",
    ols_fe_re_r2        = "atol=1e-5",
    logit_probit_coef   = "atol=1e-6 (MLE 収束差、statsmodels と比較)",
    iv_coef             = "atol=1e-8 (AER::ivreg vs linearmodels::IV2SLS)",
    iv_diagnostics      = "rtol=1e-4 (Wu-Hausman は F 統計量定義が異なる可能性)",
    lasso_ridge_scaled  = "atol=1e-5 (sklearn / glmnet 同一目的関数)"
  )
)

# -----------------------------------------------------------------------------
# 12. JSON 出力
# -----------------------------------------------------------------------------
benchmark_results <- list(
  meta   = meta,
  ols    = ols_result,
  fe     = fe_result,
  re     = re_result,
  logit  = logit_result,
  probit = probit_result,
  iv     = iv_result,
  lasso  = lasso_result,
  ridge  = ridge_result
)

if (!dir.exists(TARGET_DIR)) dir.create(TARGET_DIR, recursive = TRUE)

write_json(
  benchmark_results,
  OUTPUT_FILE,
  auto_unbox = TRUE, pretty = TRUE, digits = NA
)

cat(sprintf("Benchmark JSON written to: %s\n", OUTPUT_FILE))

# -----------------------------------------------------------------------------
# 13. サニティチェック
# -----------------------------------------------------------------------------
cat("\n=== OLS ===\n");    print(round(unlist(ols_result$coefficients), 6))
cat("\n=== FE ===\n");     print(round(unlist(fe_result$coefficients), 6))
cat("\n=== RE ===\n");     print(round(unlist(re_result$coefficients), 6))
cat("\n=== Logit ===\n");  print(round(unlist(logit_result$coefficients), 4))
cat("\n=== Probit ===\n"); print(round(unlist(probit_result$coefficients), 4))
cat("\n=== IV ===\n");     print(round(unlist(iv_result$coefficients), 6))
cat("\n=== Lasso scaled ===\n"); print(round(unlist(lasso_result$coef_scaled), 6))
cat("\n=== Ridge scaled ===\n"); print(round(unlist(ridge_result$coef_scaled), 6))

cat("\n=== R² / LR / IV Diagnostics ===\n")
cat(sprintf("  OLS  R²           : %.15f\n", ols_result$r_squared))
cat(sprintf("  FE   R²_within    : %.15f\n", fe_result$r_squared_within))
cat(sprintf("  RE   R²_within    : %.15f\n", re_result$r_squared_within))
cat(sprintf("  IV   R²           : %.15f\n", iv_result$r_squared))
cat(sprintf("  Logit  pseudo-R²  : %.15f\n", logit_result$pseudo_r_squared))
cat(sprintf("  Probit pseudo-R²  : %.15f\n", probit_result$pseudo_r_squared))
cat(sprintf(
  "  Logit  LR chi2(%d)= %.6f, p=%.6f\n",
  logit_result$lr_test$df, logit_result$lr_test$statistic,
  logit_result$lr_test$p_value
))
cat(sprintf(
  "  Probit LR chi2(%d)= %.6f, p=%.6f\n",
  probit_result$lr_test$df, probit_result$lr_test$statistic,
  probit_result$lr_test$p_value
))
cat(sprintf(
  "  IV Wu-Hausman F(%d,%d)  = %.6f, p=%.6f\n",
  iv_result$wu_hausman$df1, iv_result$wu_hausman$df2,
  iv_result$wu_hausman$statistic, iv_result$wu_hausman$p_value
))
cat(sprintf(
  "  IV Sargan  chi2(%d) = %.6f, p=%.6f\n",
  iv_result$sargan$df, iv_result$sargan$statistic,
  iv_result$sargan$p_value
))

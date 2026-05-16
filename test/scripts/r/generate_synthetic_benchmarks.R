#!/usr/bin/env Rscript
# =============================================================================
# generate_synthetic_benchmarks.R
# generate_synthetic_data.py が生成した合成データを用いて、R による
# ベンチマーク JSON を生成する。Python (statsmodels/linearmodels) 側の
# generate_benchmarks.py と同じ推定を行い、クロスチェックに用いる。
#
# 使い方（ワークスペースルートから）:
#   Rscript test/scripts/r/generate_synthetic_benchmarks.R
#
# 出力（推定方法ごとに1ファイル）:
#   test/benchmarks/r_synthetic_ols_gold.json
#   test/benchmarks/r_synthetic_logit_gold.json
#   test/benchmarks/r_synthetic_probit_gold.json
#   test/benchmarks/r_synthetic_lasso_gold.json
#   test/benchmarks/r_synthetic_ridge_gold.json
#   test/benchmarks/r_synthetic_fe_gold.json
#   test/benchmarks/r_synthetic_re_gold.json
#   test/benchmarks/r_synthetic_iv_gold.json
#   test/benchmarks/r_synthetic_tobit_gold.json
#   test/benchmarks/r_synthetic_heckman_gold.json
#   test/benchmarks/r_synthetic_rdd_gold.json
#
# 収録モデル:
#   OLS (nonrobust / HC1 / HAC)  - sandwich::vcovHC + sandwich::NeweyWest
#   Logit / Probit               - glm(binomial)
#   Lasso (alpha=0.1)            - glmnet (sklearn 互換 population std)
#   Ridge (alpha=0.5)            - glmnet
#   FE (固定効果)                - plm(model="within")
#   RE (変量効果)                - plm(model="random", random.method="swar")
#   IV (2SLS)                    - AER::ivreg
#   Tobit (左側打ち切り at 0)    - censReg
#   Heckman 2段階                - sampleSelection::heckit
#   RDD                          - rdrobust::rdrobust
#
# 必要パッケージ:
#   sandwich, lmtest, plm, AER, glmnet, censReg, sampleSelection,
#   rdrobust, jsonlite
# =============================================================================

suppressPackageStartupMessages({
  required <- c("sandwich", "lmtest", "plm", "AER", "glmnet",
                "censReg", "sampleSelection", "rdrobust", "jsonlite")
  for (pkg in required) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      stop(sprintf(
        "Required package '%s' not found. Run: install.packages('%s')",
        pkg, pkg
      ))
    }
    library(pkg, character.only = TRUE)
  }
})

# =============================================================================
# 0. パス設定
# =============================================================================
# commandArgs で --file= を探す（Rscript 実行時）
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", file_arg[1])))
} else {
  # RStudio source() など、--file= がない場合は getwd() に fallback
  getwd()
}
REPO_ROOT <- normalizePath(file.path(SCRIPT_DIR, "..", "..", ".."))
DATA_DIR   <- file.path(REPO_ROOT, "test", "data", "csv")
BENCH_DIR  <- file.path(REPO_ROOT, "test", "benchmarks", "r", "synthetic")

if (!dir.exists(BENCH_DIR)) dir.create(BENCH_DIR, recursive = TRUE)

out_path <- function(name) {
  file.path(BENCH_DIR, sprintf("r_synthetic_%s_gold.json", name))
}

# =============================================================================
# 1. データ読み込み
# =============================================================================
cat("Loading synthetic data...\n")
df_ols     <- read.csv(file.path(DATA_DIR, "synthetic_ols.csv"))
df_panel   <- read.csv(file.path(DATA_DIR, "synthetic_panel.csv"))
df_iv      <- read.csv(file.path(DATA_DIR, "synthetic_iv.csv"))
df_tobit   <- read.csv(file.path(DATA_DIR, "synthetic_tobit.csv"))
df_heckman <- read.csv(file.path(DATA_DIR, "synthetic_heckman.csv"))
df_rdd     <- read.csv(file.path(DATA_DIR, "synthetic_rdd.csv"))

# =============================================================================
# 2. ヘルパー関数
# =============================================================================

# (Intercept) → const に統一（Python API との対応）
norm_names <- function(x) {
  names(x) <- sub("^\\(Intercept\\)$", "const", names(x))
  x
}

coef_list <- function(m) as.list(norm_names(coef(m)))
se_list   <- function(m) as.list(norm_names(sqrt(diag(vcov(m)))))
tval_list <- function(m) {
  b  <- norm_names(coef(m))
  se <- norm_names(sqrt(diag(vcov(m))))
  as.list(b / se)
}
pval_list <- function(m) {
  b  <- norm_names(coef(m))
  se <- norm_names(sqrt(diag(vcov(m))))
  t  <- b / se
  df <- tryCatch(df.residual(m), error = function(e) Inf)
  as.list(2 * pt(-abs(t), df = df))
}
ci_list <- function(m, level = 0.95) {
  ci <- confint(m, level = level)
  rownames(ci) <- sub("^\\(Intercept\\)$", "const", rownames(ci))
  lapply(seq_len(nrow(ci)), function(i) list(lower = ci[i, 1], upper = ci[i, 2])) |>
    setNames(rownames(ci))
}
# Wald CI（glm 用）
ci_wald_list <- function(m, level = 0.95) {
  ci <- confint.default(m, level = level)
  rownames(ci) <- sub("^\\(Intercept\\)$", "const", rownames(ci))
  lapply(seq_len(nrow(ci)), function(i) list(lower = ci[i, 1], upper = ci[i, 2])) |>
    setNames(rownames(ci))
}

# sandwich ベースの SE から係数テーブルを構築
robust_summary <- function(fit, vcov_mat) {
  b   <- norm_names(coef(fit))
  se  <- norm_names(sqrt(diag(vcov_mat)))
  t   <- b / se
  df  <- df.residual(fit)
  pv  <- 2 * pt(-abs(t), df = df)
  z   <- qnorm(0.975)
  ci  <- lapply(seq_along(b), function(i)
    list(lower = b[[i]] - z * se[[i]], upper = b[[i]] + z * se[[i]])
  ) |> setNames(names(b))
  list(
    coefficients = as.list(b),
    std_errors   = as.list(se),
    t_values     = as.list(t),
    p_values     = as.list(pv),
    conf_int     = ci
  )
}

write_bench <- function(name, meta, estimates) {
  path <- out_path(name)
  payload <- list(
    meta      = c(meta, list(model = name)),
    estimates = estimates
  )
  write_json(payload, path, auto_unbox = TRUE, pretty = TRUE, digits = NA)
  cat(sprintf("    -> %s\n", basename(path)))
}

# =============================================================================
# 3. 共通メタデータ
# =============================================================================
meta_base <- list(
  generated_at          = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
  r_version             = as.character(getRversion()),
  sandwich_version      = as.character(packageVersion("sandwich")),
  plm_version           = as.character(packageVersion("plm")),
  aer_version           = as.character(packageVersion("AER")),
  glmnet_version        = as.character(packageVersion("glmnet")),
  censReg_version       = as.character(packageVersion("censReg")),
  sampleSelection_version = as.character(packageVersion("sampleSelection")),
  rdrobust_version      = as.character(packageVersion("rdrobust")),
  seed                  = 2024L,
  tolerance_guide = list(
    ols_coef            = "atol=1e-8 (nonrobust)",
    ols_se_hc1          = "atol=1e-6 (sandwich::vcovHC vs statsmodels HC1)",
    logit_probit_coef   = "atol=1e-6 (MLE 収束差)",
    fe_re_coef          = "atol=1e-8",
    iv_coef             = "atol=1e-8 (AER::ivreg vs linearmodels::IV2SLS)",
    tobit_coef          = "atol=1e-4 (censReg vs py4etrics MLE 実装差)",
    heckman_coef        = "atol=1e-6 (sampleSelection vs statsmodels 手動 2 段階)",
    rdd_coef            = "atol=1e-4 (rdrobust 共通実装なので高精度一致期待)",
    lasso_ridge_scaled  = "atol=1e-5 (sklearn / glmnet 同一目的関数)"
  )
)

# =============================================================================
# 4. OLS (nonrobust / HC1 / HAC)
#    DGP: y_cont = 3.0 + 2.5*x1 - 1.8*x2 + 0.9*x3 + ε
# =============================================================================
cat("  [1/11] OLS...\n")

fit_ols <- lm(y_cont ~ x1 + x2 + x3, data = df_ols)
s_ols   <- summary(fit_ols)

# nonrobust
nr_b  <- norm_names(coef(fit_ols))
nr_se <- norm_names(sqrt(diag(vcov(fit_ols))))
nr_t  <- nr_b / nr_se
nr_df <- df.residual(fit_ols)
nr_pv <- 2 * pt(-abs(nr_t), df = nr_df)
nr_ci <- ci_list(fit_ols)

nonrobust <- list(
  coefficients = as.list(nr_b),
  std_errors   = as.list(nr_se),
  t_values     = as.list(nr_t),
  p_values     = as.list(nr_pv),
  conf_int     = nr_ci
)

# HC1 (sandwich)
vcov_hc1 <- vcovHC(fit_ols, type = "HC1")
hc1 <- robust_summary(fit_ols, vcov_hc1)

# HAC (Newey-West, maxlags=1)
vcov_hac <- NeweyWest(fit_ols, lag = 1, prewhite = FALSE, adjust = FALSE)
hac <- robust_summary(fit_ols, vcov_hac)

# F 統計量
f_stat <- s_ols$fstatistic
ols_estimates <- list(
  dep_var       = "y_cont",
  expl_vars     = c("x1", "x2", "x3"),
  n_obs         = nrow(df_ols),
  r_squared     = s_ols$r.squared,
  adj_r_squared = s_ols$adj.r.squared,
  f_test = list(
    statistic = as.numeric(f_stat["value"]),
    df1       = as.integer(f_stat["numdf"]),
    df2       = as.integer(f_stat["dendf"]),
    p_value   = as.numeric(pf(f_stat["value"], f_stat["numdf"], f_stat["dendf"],
                               lower.tail = FALSE))
  ),
  nonrobust    = nonrobust,
  hc1          = hc1,
  hac_maxlags1 = hac
)

write_bench("ols", c(meta_base, list(data_file = "synthetic_ols.csv")), ols_estimates)

# =============================================================================
# 5. Logit
#    DGP: y_binary ~ logistic((-0.5 + 1.2*x1 - 0.8*x2 + 0.5*x3) * 0.15)
# =============================================================================
cat("  [2/11] Logit...\n")

fit_logit    <- glm(y_binary ~ x1 + x2 + x3, data = df_ols,
                    family = binomial(link = "logit"))
llf_logit    <- as.numeric(logLik(fit_logit))
llf_logit_0  <- as.numeric(logLik(
  glm(y_binary ~ 1, data = df_ols, family = binomial(link = "logit"))
))
lr_stat_logit <- fit_logit$null.deviance - fit_logit$deviance
lr_df_logit   <- fit_logit$df.null - fit_logit$df.residual

logit_b  <- norm_names(coef(fit_logit))
logit_se <- norm_names(sqrt(diag(vcov(fit_logit))))
logit_t  <- logit_b / logit_se
logit_pv <- 2 * pnorm(-abs(logit_t))  # z 検定（MLE）

logit_estimates <- list(
  dep_var             = "y_binary",
  n_obs               = nrow(df_ols),
  n_positive          = as.integer(sum(df_ols$y_binary)),
  coefficients        = as.list(logit_b),
  std_errors          = as.list(logit_se),
  t_values            = as.list(logit_t),
  p_values            = as.list(logit_pv),
  conf_int            = ci_wald_list(fit_logit),
  pseudo_r_squared    = 1 - llf_logit / llf_logit_0,
  log_likelihood      = llf_logit,
  log_likelihood_null = llf_logit_0,
  aic                 = AIC(fit_logit),
  bic                 = BIC(fit_logit),
  lr_test = list(
    statistic = lr_stat_logit,
    df        = as.integer(lr_df_logit),
    p_value   = as.numeric(pchisq(lr_stat_logit, df = lr_df_logit,
                                   lower.tail = FALSE))
  )
)

write_bench("logit", c(meta_base, list(data_file = "synthetic_ols.csv")), logit_estimates)

# =============================================================================
# 6. Probit
# =============================================================================
cat("  [3/11] Probit...\n")

fit_probit   <- glm(y_binary ~ x1 + x2 + x3, data = df_ols,
                    family = binomial(link = "probit"))
llf_probit   <- as.numeric(logLik(fit_probit))
llf_probit_0 <- as.numeric(logLik(
  glm(y_binary ~ 1, data = df_ols, family = binomial(link = "probit"))
))
lr_stat_probit <- fit_probit$null.deviance - fit_probit$deviance
lr_df_probit   <- fit_probit$df.null - fit_probit$df.residual

probit_b  <- norm_names(coef(fit_probit))
probit_se <- norm_names(sqrt(diag(vcov(fit_probit))))
probit_t  <- probit_b / probit_se
probit_pv <- 2 * pnorm(-abs(probit_t))

probit_estimates <- list(
  dep_var             = "y_binary",
  n_obs               = nrow(df_ols),
  n_positive          = as.integer(sum(df_ols$y_binary)),
  coefficients        = as.list(probit_b),
  std_errors          = as.list(probit_se),
  t_values            = as.list(probit_t),
  p_values            = as.list(probit_pv),
  conf_int            = ci_wald_list(fit_probit),
  pseudo_r_squared    = 1 - llf_probit / llf_probit_0,
  log_likelihood      = llf_probit,
  log_likelihood_null = llf_probit_0,
  aic                 = AIC(fit_probit),
  bic                 = BIC(fit_probit),
  lr_test = list(
    statistic = lr_stat_probit,
    df        = as.integer(lr_df_probit),
    p_value   = as.numeric(pchisq(lr_stat_probit, df = lr_df_probit,
                                   lower.tail = FALSE))
  )
)

write_bench("probit", c(meta_base, list(data_file = "synthetic_ols.csv")), probit_estimates)

# =============================================================================
# 7. Lasso (glmnet, alpha=0.1, sklearn 互換 population std)
#    sklearn: Pipeline([StandardScaler(ddof=0), Lasso(alpha=0.1)])
# =============================================================================
cat("  [4/11] Lasso (alpha=0.1)...\n")

LASSO_ALPHA <- 0.1
X_mat <- as.matrix(df_ols[, c("x1", "x2", "x3")])
y_cont <- df_ols$y_cont
n_ols  <- nrow(df_ols)

col_means_ols <- colMeans(X_mat)
col_sds_pop   <- apply(X_mat, 2, sd) * sqrt((n_ols - 1) / n_ols)
X_std_ols     <- scale(X_mat, center = col_means_ols, scale = col_sds_pop)

set.seed(2024)
fit_lasso <- glmnet(X_std_ols, y_cont,
                    alpha = 1, lambda = LASSO_ALPHA,
                    standardize = FALSE, intercept = TRUE)
lasso_coef_mat    <- as.matrix(coef(fit_lasso))
lasso_coef_scaled <- lasso_coef_mat[c("x1", "x2", "x3"), 1]
lasso_intercept_scaled <- lasso_coef_mat["(Intercept)", 1]
lasso_coef_orig   <- lasso_coef_scaled / col_sds_pop
lasso_intercept_orig <- mean(y_cont) - sum(lasso_coef_orig * col_means_ols)

lasso_estimates <- list(
  dep_var     = "y_cont",
  alpha       = LASSO_ALPHA,
  n_obs       = n_ols,
  coef_scaled = as.list(lasso_coef_scaled),
  coef_orig   = as.list(c(const = lasso_intercept_orig, lasso_coef_orig)),
  note        = paste(
    "coef_scaled は StandardScaler(ddof=0) → Lasso(alpha=0.1) の coef_ に対応。",
    "coef_orig は元スケールに逆変換した係数。"
  )
)

write_bench("lasso", c(meta_base, list(data_file = "synthetic_ols.csv")), lasso_estimates)

# =============================================================================
# 8. Ridge (glmnet, alpha=0.5, sklearn 互換)
#    sklearn: Pipeline([StandardScaler(ddof=0), Ridge(alpha=0.5)])
#    glmnet lambda = sklearn_alpha / n  (Ridge ペナルティ定義の違いを補正)
# =============================================================================
cat("  [5/11] Ridge (alpha=0.5)...\n")

RIDGE_ALPHA  <- 0.5
RIDGE_LAMBDA <- RIDGE_ALPHA / n_ols

set.seed(2024)
fit_ridge <- glmnet(X_std_ols, y_cont,
                    alpha = 0, lambda = RIDGE_LAMBDA,
                    standardize = FALSE, intercept = TRUE)
ridge_coef_mat    <- as.matrix(coef(fit_ridge))
ridge_coef_scaled <- ridge_coef_mat[c("x1", "x2", "x3"), 1]
ridge_coef_orig   <- ridge_coef_scaled / col_sds_pop
ridge_intercept_orig <- mean(y_cont) - sum(ridge_coef_orig * col_means_ols)

ridge_estimates <- list(
  dep_var      = "y_cont",
  alpha        = RIDGE_ALPHA,
  glmnet_lambda = RIDGE_LAMBDA,
  n_obs        = n_ols,
  coef_scaled  = as.list(ridge_coef_scaled),
  coef_orig    = as.list(c(const = ridge_intercept_orig, ridge_coef_orig)),
  note         = sprintf(
    "coef_scaled は StandardScaler(ddof=0) → Ridge(alpha=%.1f) の coef_ に対応。glmnet lambda = %.1f/%d = %.6f",
    RIDGE_ALPHA, RIDGE_ALPHA, n_ols, RIDGE_LAMBDA
  )
)

write_bench("ridge", c(meta_base, list(data_file = "synthetic_ols.csv")), ridge_estimates)

# =============================================================================
# 9. 固定効果 (FE) — plm within
#    DGP: y = 1.0 + 3.0*x1 - 2.0*x2 + alpha_i + ε
# =============================================================================
cat("  [6/11] Fixed Effects (FE)...\n")

# panel データ（entity_id, time_id がインデックス）
df_panel$entity_id <- as.factor(df_panel$entity_id)
df_panel$time_id   <- as.factor(df_panel$time_id)
pdata <- pdata.frame(df_panel, index = c("entity_id", "time_id"))

fit_fe <- plm(y ~ x1 + x2, data = pdata, model = "within")
s_fe   <- summary(fit_fe)

fe_b  <- coef(fit_fe)
fe_se <- sqrt(diag(vcov(fit_fe)))
fe_t  <- fe_b / fe_se
fe_df <- s_fe$df[2]
fe_pv <- 2 * pt(-abs(fe_t), df = fe_df)
fe_ci <- lapply(seq_along(fe_b), function(i) {
  crit <- qt(0.975, df = fe_df)
  list(lower = fe_b[i] - crit * fe_se[i], upper = fe_b[i] + crit * fe_se[i])
}) |> setNames(names(fe_b))

# clustered SE (entity)
vcov_cl <- vcovHC(fit_fe, type = "HC1", cluster = "group")
fe_cl_se <- sqrt(diag(vcov_cl))
fe_cl_t  <- fe_b / fe_cl_se
fe_cl_df <- length(unique(df_panel$entity_id)) - 1L
fe_cl_pv <- 2 * pt(-abs(fe_cl_t), df = fe_cl_df)
fe_cl_ci <- lapply(seq_along(fe_b), function(i) {
  crit <- qt(0.975, df = fe_cl_df)
  list(lower = fe_b[i] - crit * fe_cl_se[i],
       upper = fe_b[i] + crit * fe_cl_se[i])
}) |> setNames(names(fe_b))

fe_estimates <- list(
  n_obs              = as.integer(nrow(pdata)),
  n_entities         = as.integer(length(unique(df_panel$entity_id))),
  n_periods          = as.integer(length(unique(df_panel$time_id))),
  r_squared_within   = as.numeric(s_fe$r.squared["rsq"]),
  r_squared_between  = as.numeric(summary(fit_fe, multipart = FALSE)$r.sq.between),
  r_squared_overall  = as.numeric(summary(fit_fe, multipart = FALSE)$r.sq.overall),
  f_test = list(
    statistic = as.numeric(s_fe$fstatistic$statistic),
    p_value   = as.numeric(s_fe$fstatistic$p.value)
  ),
  nonrobust = list(
    coefficients = as.list(fe_b),
    std_errors   = as.list(fe_se),
    t_values     = as.list(fe_t),
    p_values     = as.list(fe_pv),
    conf_int     = fe_ci
  ),
  clustered_entity = list(
    coefficients = as.list(fe_b),
    std_errors   = as.list(fe_cl_se),
    t_values     = as.list(fe_cl_t),
    p_values     = as.list(fe_cl_pv),
    conf_int     = fe_cl_ci
  )
)

write_bench("fe", c(meta_base, list(data_file = "synthetic_panel.csv")), fe_estimates)

# =============================================================================
# 10. 変量効果 (RE) — plm Swamy-Arora
# =============================================================================
cat("  [7/11] Random Effects (RE)...\n")

fit_re <- plm(y ~ x1 + x2, data = pdata,
              model = "random", random.method = "swar")
s_re   <- summary(fit_re)

re_b  <- norm_names(coef(fit_re))
re_se <- norm_names(sqrt(diag(vcov(fit_re))))
re_t  <- re_b / re_se
re_df <- Inf  # RE は漸近 z 検定
re_pv <- 2 * pnorm(-abs(re_t))
z_crit <- qnorm(0.975)
re_ci <- lapply(seq_along(re_b), function(i) {
  list(lower = re_b[[i]] - z_crit * re_se[[i]],
       upper = re_b[[i]] + z_crit * re_se[[i]])
}) |> setNames(names(re_b))

# theta (GLS 変換パラメータ)
theta_val <- as.numeric(fit_re$ercomp$theta)

re_estimates <- list(
  n_obs             = as.integer(nrow(pdata)),
  r_squared_within  = as.numeric(s_re$r.squared["rsq"]),
  r_squared_between = as.numeric(summary(fit_re, multipart = FALSE)$r.sq.between),
  r_squared_overall = as.numeric(summary(fit_re, multipart = FALSE)$r.sq.overall),
  theta             = theta_val,
  nonrobust = list(
    coefficients = as.list(re_b),
    std_errors   = as.list(re_se),
    t_values     = as.list(re_t),
    p_values     = as.list(re_pv),
    conf_int     = re_ci
  )
)

write_bench("re", c(meta_base, list(data_file = "synthetic_panel.csv")), re_estimates)

# =============================================================================
# 11. IV 2SLS (AER::ivreg)
#     DGP: y = 2.0 + 1.5*x_exog + 3.0*x_endog + u
#     Instruments: z1, z2 for x_endog
# =============================================================================
cat("  [8/11] IV (2SLS)...\n")

fit_iv    <- ivreg(y ~ x_exog + x_endog | x_exog + z1 + z2, data = df_iv)
s_iv_diag <- summary(fit_iv, diagnostics = TRUE)

iv_b  <- norm_names(coef(fit_iv))
iv_se <- norm_names(sqrt(diag(vcov(fit_iv))))
iv_t  <- iv_b / iv_se
iv_df <- df.residual(fit_iv)
iv_pv <- 2 * pt(-abs(iv_t), df = iv_df)
iv_ci_raw <- confint(fit_iv)
rownames(iv_ci_raw) <- sub("^\\(Intercept\\)$", "const", rownames(iv_ci_raw))
iv_ci <- lapply(seq_len(nrow(iv_ci_raw)), function(i)
  list(lower = iv_ci_raw[i, 1], upper = iv_ci_raw[i, 2])
) |> setNames(rownames(iv_ci_raw))

iv_rss <- sum(residuals(fit_iv)^2)
iv_tss <- sum((df_iv$y - mean(df_iv$y))^2)

# HC1
vcov_iv_hc1 <- vcovHC(fit_iv, type = "HC1")
iv_hc1 <- robust_summary(fit_iv, vcov_iv_hc1)

# First-stage diagnostics (Wu-Hausman, Sargan)
diag_m <- s_iv_diag$diagnostics

iv_estimates <- list(
  dep_var    = "y",
  exog_vars  = "x_exog",
  endog_vars = "x_endog",
  instruments = c("z1", "z2"),
  n_obs      = nrow(df_iv),
  r_squared  = 1 - iv_rss / iv_tss,
  nonrobust = list(
    coefficients = as.list(iv_b),
    std_errors   = as.list(iv_se),
    t_values     = as.list(iv_t),
    p_values     = as.list(iv_pv),
    conf_int     = iv_ci
  ),
  hc1 = iv_hc1,
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

write_bench("iv", c(meta_base, list(data_file = "synthetic_iv.csv")), iv_estimates)

# =============================================================================
# 12. Tobit (censReg, 左側打ち切り at 0)
#     DGP: y_latent = 2.0 + 2.0*x1 + 1.5*x2 + ε, y = max(0, y_latent)
# =============================================================================
cat("  [9/11] Tobit...\n")

fit_tobit <- censReg(y ~ x1 + x2, left = 0, right = Inf, data = df_tobit)
s_tobit   <- summary(fit_tobit)

# censReg params: [beta..., logSigma]
tobit_coef <- coef(fit_tobit)   # 最後が logSigma
tobit_se   <- sqrt(diag(vcov(fit_tobit)))
n_coef     <- length(tobit_coef) - 1L  # logSigma 除外
var_names  <- c("const", "x1", "x2")

tobit_b  <- norm_names(tobit_coef[seq_len(n_coef)])
tobit_se2 <- tobit_se[seq_len(n_coef)]
names(tobit_se2) <- names(tobit_b)
tobit_t  <- tobit_b / tobit_se2
tobit_pv <- 2 * pnorm(-abs(tobit_t))
z_crit   <- qnorm(0.975)
tobit_ci <- lapply(seq_along(tobit_b), function(i)
  list(lower = tobit_b[[i]] - z_crit * tobit_se2[[i]],
       upper = tobit_b[[i]] + z_crit * tobit_se2[[i]])
) |> setNames(names(tobit_b))

sigma_val <- exp(as.numeric(tobit_coef["logSigma"]))
cens_ratio <- mean(df_tobit$y <= 0)

tobit_llf <- as.numeric(logLik(fit_tobit))
tobit_estimates <- list(
  dep_var              = "y",
  left_censoring_limit = 0.0,
  n_obs                = nrow(df_tobit),
  censoring_ratio      = cens_ratio,
  sigma                = sigma_val,
  log_likelihood       = tobit_llf,
  aic                  = -2 * tobit_llf + 2 * (n_coef + 1L),
  bic                  = -2 * tobit_llf + log(nrow(df_tobit)) * (n_coef + 1L),
  coefficients         = as.list(tobit_b),
  std_errors           = as.list(tobit_se2),
  t_values             = as.list(tobit_t),
  p_values             = as.list(tobit_pv),
  conf_int             = tobit_ci
)

write_bench("tobit", c(meta_base, list(data_file = "synthetic_tobit.csv")), tobit_estimates)

# =============================================================================
# 13. Heckman 2段階 (sampleSelection::heckit)
#     Step 1 (selection): employed ~ educ + exp + kids
#     Step 2 (outcome):   wage ~ educ + exp  (+IMR)
# =============================================================================
cat("  [10/11] Heckman 2-step...\n")

df_heck <- df_heckman
df_heck$employed <- as.integer(df_heck$employed)

fit_heck <- heckit(
  selection = employed ~ educ + exp + kids,
  outcome   = wage ~ educ + exp,
  data      = df_heck,
  method    = "2step"
)
s_heck <- summary(fit_heck)

# Step 1: Probit (selection)
sel_b  <- norm_names(coef(fit_heck$probit))
sel_se <- norm_names(sqrt(diag(vcov(fit_heck$probit))))
sel_t  <- sel_b / sel_se
sel_pv <- 2 * pnorm(-abs(sel_t))
z_crit <- qnorm(0.975)
sel_ci <- lapply(seq_along(sel_b), function(i)
  list(lower = sel_b[[i]] - z_crit * sel_se[[i]],
       upper = sel_b[[i]] + z_crit * sel_se[[i]])
) |> setNames(names(sel_b))

llf_probit_sel   <- as.numeric(logLik(fit_heck$probit))
llf_probit_sel_0 <- as.numeric(logLik(
  glm(employed ~ 1, data = df_heck, family = binomial(link = "probit"))
))

# Step 2: OLS (outcome + IMR)
# sampleSelection の outcome 部分 coef には IMR (invMillsRatio) が含まれる
out_coef_full <- coef(fit_heck)
out_se_full   <- sqrt(diag(vcov(fit_heck)))
# 変数名正規化
names(out_coef_full) <- sub("^\\(Intercept\\)$", "const", names(out_coef_full))
names(out_se_full)   <- sub("^\\(Intercept\\)$", "const", names(out_se_full))

# outcome 部分のみ取得（selection 除く）
out_vars <- c("const", "educ", "exp", "invMillsRatio")
out_b    <- out_coef_full[out_vars]
out_se   <- out_se_full[out_vars]
out_t    <- out_b / out_se
out_pv   <- 2 * pt(-abs(out_t), df = sum(df_heck$employed, na.rm = TRUE) - length(out_vars))
out_ci   <- lapply(seq_along(out_b), function(i) {
  crit <- qt(0.975, df = sum(df_heck$employed, na.rm = TRUE) - length(out_vars))
  list(lower = out_b[[i]] - crit * out_se[[i]],
       upper = out_b[[i]] + crit * out_se[[i]])
}) |> setNames(names(out_b))

n_selected <- as.integer(sum(df_heck$employed, na.rm = TRUE))
imr_name   <- "invMillsRatio"

heckman_estimates <- list(
  n_total      = nrow(df_heck),
  n_selected   = n_selected,
  selection_ratio = n_selected / nrow(df_heck),
  step1_probit = list(
    dep_var         = "employed",
    sel_vars        = c("educ", "exp", "kids"),
    n_obs           = nrow(df_heck),
    coefficients    = as.list(sel_b),
    std_errors      = as.list(sel_se),
    t_values        = as.list(sel_t),
    p_values        = as.list(sel_pv),
    conf_int        = sel_ci,
    pseudo_r_squared = 1 - llf_probit_sel / llf_probit_sel_0,
    log_likelihood  = llf_probit_sel
  ),
  step2_ols = list(
    dep_var      = "wage",
    outcome_vars = c("educ", "exp"),
    n_obs        = n_selected,
    coefficients = as.list(out_b),
    std_errors   = as.list(out_se),
    t_values     = as.list(out_t),
    p_values     = as.list(out_pv),
    conf_int     = out_ci
  ),
  imr = list(
    coefficient = as.numeric(out_b[imr_name]),
    std_error   = as.numeric(out_se[imr_name]),
    t_value     = as.numeric(out_t[imr_name]),
    p_value     = as.numeric(out_pv[imr_name])
  )
)

write_bench("heckman", c(meta_base, list(data_file = "synthetic_heckman.csv")), heckman_estimates)

# =============================================================================
# 14. RDD (rdrobust)
#     DGP: y = 2.0 + 1.5*running_var + 5.0*treat + ε  (treat = 1[x>=0])
#     cutoff = 0.0, 真の処置効果 = 5.0
# =============================================================================
cat("  [11/11] RDD (rdrobust)...\n")

cutoff <- 0.0
res_rdd <- rdrobust(df_rdd$y, df_rdd$running_var, c = cutoff)

coef_conv <- res_rdd$coef[1, 1]
coef_bc   <- res_rdd$coef[2, 1]
coef_rob  <- res_rdd$coef[3, 1]

se_conv <- res_rdd$se[1, 1]
se_bc   <- res_rdd$se[2, 1]
se_rob  <- res_rdd$se[3, 1]

t_conv  <- res_rdd$t[1, 1]
t_bc    <- res_rdd$t[2, 1]
t_rob   <- res_rdd$t[3, 1]

pv_conv <- res_rdd$pv[1, 1]
pv_bc   <- res_rdd$pv[2, 1]
pv_rob  <- res_rdd$pv[3, 1]

ci_conv <- c(res_rdd$ci[1, 1], res_rdd$ci[1, 2])
ci_bc   <- c(res_rdd$ci[2, 1], res_rdd$ci[2, 2])
ci_rob  <- c(res_rdd$ci[3, 1], res_rdd$ci[3, 2])

bw_left       <- res_rdd$bws["h", "left"]
bw_right      <- res_rdd$bws["h", "right"]
bw_bias_left  <- res_rdd$bws["b", "left"]
bw_bias_right <- res_rdd$bws["b", "right"]

rdd_estimates <- list(
  dep_var     = "y",
  running_var = "running_var",
  cutoff      = cutoff,
  n_total     = length(df_rdd$y),
  n_left      = as.integer(res_rdd$N_h[1]),
  n_right     = as.integer(res_rdd$N_h[2]),
  bandwidth = list(
    bw_left       = bw_left,
    bw_right      = bw_right,
    bw_bias_left  = bw_bias_left,
    bw_bias_right = bw_bias_right
  ),
  conventional = list(
    coef     = coef_conv,
    std_err  = se_conv,
    t_stat   = t_conv,
    p_value  = pv_conv,
    ci_lower = ci_conv[1],
    ci_upper = ci_conv[2]
  ),
  bias_corrected = list(
    coef     = coef_bc,
    std_err  = se_bc,
    t_stat   = t_bc,
    p_value  = pv_bc,
    ci_lower = ci_bc[1],
    ci_upper = ci_bc[2]
  ),
  robust = list(
    coef     = coef_rob,
    std_err  = se_rob,
    t_stat   = t_rob,
    p_value  = pv_rob,
    ci_lower = ci_rob[1],
    ci_upper = ci_rob[2]
  )
)

write_bench("rdd", c(meta_base, list(data_file = "synthetic_rdd.csv")), rdd_estimates)

# =============================================================================
# 15. サニティチェック
# =============================================================================
cat("\n=== Benchmark Summary (R) ===\n")
cat("OLS  (true: const=3.0, x1=2.5, x2=-1.8, x3=0.9)\n")
cat(sprintf("  const=%.4f, x1=%.4f, x2=%.4f, x3=%.4f\n",
            ols_estimates$nonrobust$coefficients$const,
            ols_estimates$nonrobust$coefficients$x1,
            ols_estimates$nonrobust$coefficients$x2,
            ols_estimates$nonrobust$coefficients$x3))

cat("FE   (true: x1=3.0, x2=-2.0)\n")
cat(sprintf("  x1=%.4f, x2=%.4f\n",
            fe_estimates$nonrobust$coefficients$x1,
            fe_estimates$nonrobust$coefficients$x2))

cat("IV   (true: const=2.0, x_exog=1.5, x_endog=3.0)\n")
cat(sprintf("  const=%.4f, x_exog=%.4f, x_endog=%.4f\n",
            iv_estimates$nonrobust$coefficients$const,
            iv_estimates$nonrobust$coefficients$x_exog,
            iv_estimates$nonrobust$coefficients$x_endog))

cat("RDD  (true effect=5.0)\n")
cat(sprintf("  conventional=%.4f, bias_corrected=%.4f\n",
            rdd_estimates$conventional$coef,
            rdd_estimates$bias_corrected$coef))

cat("\nDone.\n")

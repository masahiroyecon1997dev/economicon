# 必要なライブラリのインストール
# Ctrl + Shift + Sか右上の再生ボタンで実行
# install.packages(c("plm", "fixest", "jsonlite"))

library(plm)
library(fixest)
library(jsonlite)

# データの読み込み
data("Grunfeld", package = "plm")

# 1. OLS (Pooled OLS)
model_ols <- lm(inv ~ value + capital, data = Grunfeld)

# 2. Fixed Effects (Within)
# Rのplmパッケージを使用
model_fe <- plm(inv ~ value + capital, data = Grunfeld,
                index = c("firm", "year"), model = "within")

# 3. Random Effects
model_re <- plm(inv ~ value + capital, data = Grunfeld,
                index = c("firm", "year"), model = "random")

# 4. IV (2SLS) - capitalを内生変数、valueのラグを操作変数と仮定（テスト用）
# 実際にはfixestのfeolsがIVも扱えるのでそちらを推奨
model_iv <- feols(inv ~ value | capital ~ lag(value), data = Grunfeld)

# 統計量の抽出関数
get_stats <- function(m) {
  s <- summary(m)
  # パッケージによって構造が違うため、共通の形式に整形
  list(
    coefficients = as.list(coef(m)),
    std_errors = as.list(sqrt(diag(vcov(m)))),
    r_squared = if(!is.null(s$r.squared)) s$r.squared else s$sq.cor
  )
}

# JSONとしてまとめる
benchmark_results <- list(
  ols = get_stats(model_ols),
  fe = get_stats(model_fe),
  re = get_stats(model_re),
  iv = get_stats(model_iv)
)

# 保存
target_dir <- file.path(getwd(), "rcode", "tests", "benchmarks")
if (!dir.exists(target_dir)) {
  dir.create(target_dir, recursive = TRUE)
}
file_path <- file.path(target_dir, "r_grunfeld_gold.json")

write_json(benchmark_results, file_path, auto_unbox = TRUE, pretty = TRUE)

print("Benchmark JSON generated successfully.")

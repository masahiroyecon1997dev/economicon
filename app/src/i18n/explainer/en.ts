import type { ExplainerContentMap } from "./types";

export const enExplainer = {
  confidence_interval: {
    title: "What Is a Confidence Interval?",
    body: `A confidence interval gives you an upper and lower bound for an estimated value. Typically, 90%, 95%, or 99% intervals are used.

When you hear "95% confidence interval", it's tempting to think "there is a 95% probability that the true value lies within this interval" — but this is incorrect. In frequentist statistics, the true value is a single fixed number. What varies is the confidence interval itself (both its upper and lower bounds) calculated from our data.

The correct interpretation: "If we repeated this with 100 independent datasets, approximately 95 of the resulting intervals would contain the true fixed value." This is the meaning of a 95% confidence interval.

### Why use the distribution of the estimator?

The width of a confidence interval is not determined by the spread of the raw data, but by the sampling distribution — how the estimated mean or coefficient would vary across hypothetical repeated samples.

As sample size increases, estimated values cluster more tightly around the true value. We use this "spread of the estimator (standard error)" to determine the interval width.

### Why the estimator follows a bell-shaped distribution

On the shape of the estimator's distribution:

Small samples (n), data approximately normal: By the Student-Fisher theorem, the standardized estimator follows a t-distribution (a bell curve with slightly heavier tails) exactly. This is a mathematical result derived from the normality assumption — not the Central Limit Theorem. Note: for small samples with non-normal data, the t-distribution may not be appropriate.

Large samples (n): Regardless of how skewed the raw data is, the Central Limit Theorem tells us that the estimator's distribution converges toward a normal (Gaussian) bell curve. Note that "large enough" depends on the shape of the data distribution.

Because the estimator distribution becomes bell-shaped, we can calculate the exact interval width that will capture the true value approximately 95% of the time.

### Connection to hypothesis tests, t-values and p-values

The confidence interval framework is the flip side of hypothesis testing, t-values, and p-values.

Hypothesis testing asks: "Is the effect of this variable truly zero?" (null hypothesis).

If the 95% confidence interval does not contain 0, the estimated value is far enough from zero that the interval cannot capture it. In this case:
• p-value ≤ 0.05 (5%)
• |t-value| ≥ 1.96 for large samples (normal approximation), or ≥ degrees-of-freedom-dependent critical value (typically > 2) for small samples (t-distribution)

Conclusion: "The effect is statistically significant (we cannot claim it is zero)."`,
  },
  mean: {
    title: "Confidence Interval for the Mean (t-distribution)",
    body: `Computes a confidence interval for the population mean μ using the sample mean x̄ as a point estimate. Applies when data come from a normal distribution or the sample size is large (central limit theorem).

$$
\\bar{x} \\pm t_{\\alpha/2,\\, n-1} \\cdot \\frac{s}{\\sqrt{n}}
$$

**Assumptions**

Data are i.i.d. (independently and identically distributed). For small samples the distribution should be approximately normal.`,
  },
  median: {
    title: "Confidence Interval for the Median (Bootstrap)",
    body: `Estimates the confidence interval for the median using the Bootstrap method (1,000 resamples). This is a non-parametric approach that requires no distributional assumptions.

$$
\\left[\\hat{m}^*_{(\\alpha/2)},\\;\\hat{m}^*_{(1-\\alpha/2)}\\right]
$$

**Assumptions**

Data should be a representative sample of the population. Accuracy decreases for very small samples.`,
  },
  proportion: {
    title: "Confidence Interval for a Proportion (Wilson Score)",
    body: `Computes the Wilson score interval for the success proportion p̂ of binary data (0 or 1 only). Outperforms the Wald interval in small-sample coverage. The column must contain only 0 and 1 values.

$$
\\frac{\\hat{p} + \\dfrac{z^2}{2n} \\pm z\\sqrt{\\dfrac{\\hat{p}(1-\\hat{p})}{n} + \\dfrac{z^2}{4n^2}}}{1 + \\dfrac{z^2}{n}}
$$

**Assumptions**

Column values must be binary (0 or 1 only). The API will return an error if other values are present.`,
  },
  variance: {
    title: "Confidence Interval for the Variance (Chi-squared)",
    body: `Computes a confidence interval for the population variance σ² using the sample variance s² and the chi-squared distribution. Exact when data are normally distributed.

$$
\\left[\\frac{(n-1)s^2}{\\chi^2_{\\alpha/2,\\, n-1}},\\;\\frac{(n-1)s^2}{\\chi^2_{1-\\alpha/2,\\, n-1}}\\right]
$$

**Assumptions**

Data must be normally distributed. Coverage degrades when the normality assumption is violated.`,
  },
  standard_deviation: {
    title: "Confidence Interval for the Standard Deviation",
    body: `Derives the confidence interval for the standard deviation σ as the square root of the variance CI bounds. The same normality assumption as the variance CI applies.

$$
\\left[\\sqrt{\\text{CI}_{\\text{lower}}(\\sigma^2)},\\;\\sqrt{\\text{CI}_{\\text{upper}}(\\sigma^2)}\\right]
$$

**Assumptions**

Data must be normally distributed (same as the variance CI assumption).`,
  },
  // ---------------------------------------------------------------------------
  // Descriptive statistics · correlation · group statistics
  // ---------------------------------------------------------------------------
  descriptive_stats_primary: {
    title: "What Are the Common Descriptive Statistics?",
    body: `Descriptive statistics summarize the key characteristics of a dataset in numerical form. Before any analysis, use these statistics to understand the scale, center, spread, and completeness of your variables.

[count] The number of non-missing (valid) observations. Use this to confirm your effective sample size.

[mean] The sum of all values divided by the count. It is sensitive to outliers, which can pull it away from the typical value.

[median] The middle value when data are sorted in ascending order. It is robust to outliers and gives a better picture of the typical value for skewed distributions (e.g., income, prices).

### std_dev · min · max

[std_dev (Standard Deviation)] The most basic measure of dispersion around the mean. A larger value means data are more spread out. It shares the same unit as the original data, making it easy to interpret.

[min / max (Minimum / Maximum)] The endpoints of the data range. Use them to quickly spot potential outliers or logical inconsistencies (e.g., negative values for age).

### Using null_count and null_ratio to Assess Missing Data Impact

[null_count] The number of missing values (NaN / NULL). A high count signals that the missing-value handling strategy will substantially affect your results.

[null_ratio] The proportion of missing values out of all rows (0–1). Including high-null-ratio columns as predictors can dramatically reduce your effective sample size through listwise deletion. When data are Missing Not At Random (MNAR), listwise deletion can also introduce estimation bias. null_ratio is the first checkpoint for data quality assessment.`,
  },
  descriptive_stats_advanced: {
    title: "What Are the Advanced Descriptive Statistics?",
    body: `Advanced statistics go beyond mean and standard deviation to characterize the shape of the distribution — asymmetry, outlier behavior, and tail thickness — which are invisible to basic summaries.

[mode] The most frequently occurring value. Especially useful for categorical or integer variables. Its interpretation weakens for continuous variables.

[variance] The square of the standard deviation. Its unit is the square of the data's unit, making it less intuitive to interpret directly, but mathematically convenient (variance is additive for independent random variables).

### range · IQR · population_variance

[range] Maximum − minimum. The simplest measure of spread, but extremely sensitive to outliers.

[iqr (Interquartile Range)] 75th percentile − 25th percentile. A robust measure of spread that is unaffected by extreme values — it equals the height of the box in a boxplot.

[population_variance] Variance divided by n (not n−1). The sample variance (÷ n−1) is an unbiased estimator of population variance, while population_variance is a descriptive measure of the full dataset's spread.

### Diagnosing Distribution Shape with Skewness and Excess Kurtosis

[skewness] Measures the asymmetry of the distribution. Positive skewness (right-skewed, long right tail) indicates a few large values pulling the mean upward; negative skewness indicates the reverse. A normal distribution has skewness = 0.

[kurtosis (Excess Kurtosis)] Measures the peakedness and tail thickness relative to a normal distribution (excess = 0). Positive values (leptokurtic) indicate heavier tails with more extreme observations than a normal distribution would produce. Together, skewness and excess kurtosis help verify OLS residual normality and guide the choice of an appropriate distributional family.`,
  },
  correlation_matrix: {
    title: "Why Look at a Correlation Matrix?",
    body: `A correlation matrix displays the pairwise linear association between all variables in your dataset — showing at a glance which variables tend to move together.

Pearson's correlation coefficient r ranges from −1 to +1. Values near +1 indicate a strong positive linear relationship; values near −1, a strong negative linear relationship; values near 0, little or no linear association. Common benchmarks: |r| ≥ 0.7 = strong, 0.4–0.7 = moderate, < 0.4 = weak — though these vary by field and sample size.

Reviewing the correlation matrix before regression helps you: (1) identify which predictors correlate with the outcome, (2) detect pairs of predictors with high mutual correlation (a warning sign for multicollinearity), and (3) check whether association signs match theoretical expectations.

### Detecting Multicollinearity

When two predictors have |r| > 0.8, multicollinearity is suspected. Multicollinearity does not bias OLS estimates, but inflates their variances — standard errors increase, t-statistics shrink, and genuinely significant variables may appear non-significant.

The correlation matrix is the first diagnostic step. For a more rigorous assessment, compute the Variance Inflation Factor (VIF) for each predictor.

### Limitations and Caveats

① Correlation ≠ causation. Even if x and y are highly correlated, x may not cause y. A confounder could be driving both.

② Sensitive to outliers. A single extreme observation can dramatically change Pearson's r. Spearman's rank correlation (ρ) is a robust alternative.

③ Cannot capture non-linear relationships. r ≈ 0 does not rule out a strong non-linear pattern (e.g., U-shaped). Always complement the matrix with scatter plots.`,
  },
  group_statistics: {
    title: "Why Look at Group-Level Statistics?",
    body: `Group-level statistics break the data down by a categorical grouping variable and compute summary statistics separately for each group. This lets you quickly compare subgroups — e.g., men vs. women, regions, treatment vs. control.

Checking group balance is a critical pre-analysis step. In causal inference settings (e.g., program evaluation), verifying that treatment and control groups have similar baseline characteristics is essential for the validity of the analysis.

Group statistics also serve as an exploratory tool for detecting subgroup-specific patterns and potential Heterogeneous Treatment Effects (HTE) that would be masked by overall averages.

### Checking for Missing-Data Patterns and Selection Bias

Comparing null_count and null_ratio across groups reveals whether missingness is systematically concentrated in particular subgroups. If a specific group has a disproportionately high missing rate, that group may be systematically excluded from estimation, introducing selection bias.

When missingness is not Missing Completely At Random (MCAR) — particularly if it is Missing Not At Random (MNAR), meaning the probability of being missing depends on the unobserved outcome itself — simple listwise deletion produces biased estimates.

### Group Differences ≠ Causal Effects

Even a statistically significant group difference does not imply that group membership causes the difference. As long as confounders simultaneously influence both the grouping variable and the outcome, any observed group difference is merely an observational correlation.

To make causal claims from group differences, appropriate causal inference methods are needed: Difference-in-Differences (DiD), Regression Discontinuity Design (RDD), propensity score matching (PSM), or randomized experiments.`,
  },
  // ---------------------------------------------------------------------------
  // Hypothesis testing
  // ---------------------------------------------------------------------------
  statistical_test: {
    title: "What Is Hypothesis Testing?",
    body: `Hypothesis testing is a formal procedure for using data to evaluate whether a stated claim about a population is statistically supported. You specify a null hypothesis (H₀: no effect, no difference) and an alternative hypothesis (H₁: there is an effect or difference), then quantify how inconsistent the data are with H₀.

The significance level α sets the maximum probability of falsely rejecting H₀ when it is actually true (Type I error). The conventional choice is α = 0.05. If the computed test statistic exceeds the critical value — equivalently, if the p-value falls below α — you reject H₀.

Confidence intervals and hypothesis tests are two sides of the same coin. Testing H₀: effect = 0 at α = 0.05 is equivalent to checking whether the 95% confidence interval excludes 0. The confidence interval is generally more informative, because it also conveys the magnitude and precision of the estimated effect.

### Choosing Between t, z, and F Tests

[t-test] Use when testing hypotheses about means with unknown population variance, particularly in small-to-moderate samples. The test statistic follows a t-distribution whose shape depends on the degrees of freedom. In large samples, the t-distribution converges to the standard normal.

[z-test] Use when population variance is known, or when samples are large enough (n ≥ 30–50 as a rule of thumb) for the Central Limit Theorem to justify the normal approximation. In practice, the t-test is almost always preferred.

[F-test / ANOVA] Use to simultaneously test equality of three or more group means, or to test joint linear restrictions on OLS coefficients. The F-statistic is the ratio of between-group variance to within-group variance.

### Common Misinterpretations of p-values

The p-value is the probability of observing data at least as extreme as what was obtained, assuming H₀ is true. It is NOT the probability that H₀ is true, nor the probability that the effect is zero.

Statistical significance (p < 0.05) does not imply practical or economic significance. With a very large sample, even a trivially small effect can yield p < 0.05. Always report effect sizes (e.g., Cohen's d) and confidence intervals alongside p-values.

Failing to reject H₀ (p ≥ 0.05) is not evidence that H₀ is true — only that the available data are insufficient to reject it. Absence of evidence is not evidence of absence.`,
  },
  statistical_test_t_test: {
    title: "What Is the t-Test?",
    body: `The t-test is the most fundamental procedure for testing hypotheses about means. It answers either 'Is the population mean equal to a specified value?' (one-sample) or 'Are the means of two groups equal?' (two-sample).

[One-sample t-test] Measures how many standard errors the sample mean x̄ lies from the hypothesized value μ₀. Under H₀: μ = μ₀, the test statistic t follows a t-distribution with n−1 degrees of freedom.

[Two-sample Welch t-test] Tests whether the means of two independent groups differ. Welch's t-test does not require equal variances, making it more general than Student's pooled-variance t-test. Welch's degrees of freedom are approximated by the Welch-Satterthwaite equation. Welch's test is the recommended default.

$$
\\begin{aligned}
t_{\\text{1-samp}} &= \\frac{\\bar{x} - \\mu_0}{s/\\sqrt{n}} \\sim t_{n-1}\\\\[6pt]
t_{\\text{Welch}} &= \\frac{\\bar{x}_1 - \\bar{x}_2}{\\sqrt{s_1^2/n_1 + s_2^2/n_2}}
\\end{aligned}
$$

**Assumptions**

① Data are i.i.d. (independently and identically distributed). ② For small samples (n ≲ 30), data should be approximately normally distributed; for large samples the Central Limit Theorem relaxes this. ③ Welch's t-test does not require equal variances; Student's pooled t-test does.`,
  },
  statistical_test_z_test: {
    title: "What Is the z-Test?",
    body: `The z-test evaluates hypotheses about a population mean using the standard normal distribution. It applies when the population variance σ² is known, or when the sample size is large enough (n ≥ 30–50 as a guideline) for the Central Limit Theorem to justify the normal approximation.

Under H₀: μ = μ₀, the test statistic z = (x̄ − μ₀) / (σ/√n) follows a standard normal distribution N(0,1). When σ is unknown and is replaced by the sample standard deviation s, the t-test is formally more appropriate.

In practice, the population variance is almost never known, so the t-test is the standard choice. For large samples (n → ∞), the t-distribution converges to the standard normal, making the z-test and t-test essentially equivalent.

$$
z = \\frac{\\bar{x} - \\mu_0}{\\sigma/\\sqrt{n}} \\sim \\mathcal{N}(0,1)
$$

**Assumptions**

① Population variance σ² is known (or the sample is large and s is used as an approximation). ② Observations are i.i.d. ③ The normality assumption is relaxed in large samples by the Central Limit Theorem.`,
  },
  statistical_test_f_test: {
    title: "What Is the F-Test / ANOVA?",
    body: `The F-test (Analysis of Variance; ANOVA) tests whether three or more populations share the same mean. The key idea is to compare between-group variation (how much group means deviate from the overall mean) with within-group variation (how much individual observations deviate from their group mean).

The F-statistic is defined as the ratio of the between-group mean square to the within-group mean square. Under H₀: μ₁ = μ₂ = … = μₖ, the F-statistic follows an F-distribution with (k−1, n−k) degrees of freedom.

A significant F-test tells you that at least one group mean differs from the others, but not which pairs differ. Post-hoc tests (Tukey HSD, Bonferroni correction, etc.) are needed to identify specific pairwise differences — addressing the multiple-comparisons problem that arises when running many pairwise t-tests.

$$
F = \\frac{\\mathrm{MS}_{\\mathrm{between}}}{\\mathrm{MS}_{\\mathrm{within}}} = \\frac{\\displaystyle\\sum_{j=1}^{k} n_j(\\bar{x}_j - \\bar{x})^2/(k-1)}{\\displaystyle\\sum_{j=1}^{k}\\sum_{i=1}^{n_j}(x_{ij}-\\bar{x}_j)^2/(n-k)} \\sim F_{k-1,\\, n-k}
$$

**Assumptions**

① Each group's data come from a normal distribution (relaxed by the CLT in large samples). ② Equal variances across groups (homoscedasticity). ③ Independence of observations. ④ If variances are unequal, use Welch's ANOVA. ⑤ For two groups, t² = F exactly, so the two-sample t-test and one-way ANOVA are equivalent.`,
  },
  // ---------------------------------------------------------------------------
  // OLS regression
  // ---------------------------------------------------------------------------
  wls_method: {
    title: "What Is Weighted Least Squares (WLS)?",
    body: `Weighted Least Squares (WLS) is an extension of OLS that assigns a weight w\u1d62 = 1/\u03c3\u00b2\u1d62 to each observation so that observations with smaller variance receive greater influence in estimation. When the heteroskedastic structure is known (or reliably estimated), WLS yields the Best Linear Unbiased Estimator (BLUE) under the Gauss\u2013Markov theorem.

Under OLS with heteroskedasticity, coefficients remain unbiased but lose minimum variance (BLUE), and the classical t/F tests are incorrect. WLS corrects for the known variance structure by scaling down the influence of high-variance observations.

### Setting Up the Weights Column

Specify a numeric column containing w\u1d62 = 1/\u03c3\u00b2\u1d62 for each row. Common strategies:

\u2460 Variance proportional to a known regressor: if Var(u\u1d62) \u221d x\u1d62, set w\u1d62 = 1/x\u1d62.

\u2461 Two-step FGLS: first run OLS, then regress squared residuals on predictors to estimate \u03c3\u00b2\u1d62, and use the inverse as weights.

\u2462 Known group variances: use the inverse of the sample variance for each group.

**Important: the weights column must contain strictly positive numeric values. Non-positive or missing values will cause an API error.**

$$
\\hat{\\beta}_{WLS} = (X'WX)^{-1}X'Wy, \\quad W = \\mathrm{diag}(w_1, \\ldots, w_n)
$$

### WLS vs OLS vs Robust Standard Errors

| Method | Assumption | BLUE | Note |
|---|---|---|---|
| OLS + Classical SE | Homoscedasticity | Under homoscedasticity only | Simplest |
| OLS + HC SE | None required | No | Unbiased estimates, valid inference |
| WLS (known structure) | Var \u221d 1/w\u1d62 | **Yes** | Most efficient when correctly specified |

If the variance structure is uncertain, OLS with HC robust standard errors is the safer default. WLS outperforms OLS only when the weights are correctly specified.`,
  },
  ols_method: {
    title: "What Is Ordinary Least Squares (OLS)?",
    body: `Ordinary Least Squares (OLS) estimates the coefficient vector β in the linear model y = Xβ + u by minimizing the sum of squared residuals Σ(yᵢ − xᵢ'β)². It is the most widely used estimation method in econometrics.

Under the Gauss-Markov assumptions (strict exogeneity, homoscedasticity, no serial correlation, no perfect multicollinearity), the OLS estimator β̂ is the Best Linear Unbiased Estimator (BLUE) — it has the smallest variance among all linear unbiased estimators.

The coefficient β̂ⱼ is interpreted as 'the average change in y when xⱼ increases by one unit, holding all other predictors constant (ceteris paribus).' This is an associational — not necessarily causal — statement.

### The Gauss-Markov Conditions

① Linearity: y = Xβ + u (linear in parameters β).

② Strict Exogeneity: E[u | X] = 0 — the error term has zero conditional mean given the regressors. Violation produces endogeneity bias, making OLS estimates inconsistent.

③ Homoscedasticity: Var(uᵢ | X) = σ² (constant). When this fails, use heteroscedasticity-robust (HC) standard errors.

④ No Serial Correlation: E[uᵢuⱼ | X] = 0 for i ≠ j. In time-series data, serial correlation of residuals is common and requires HAC standard errors.

⑤ No Perfect Multicollinearity: The regressor matrix X has full column rank (rank(X) = k).

### Causal Inference and Endogeneity

When the goal is causal estimation, the most important threat is endogeneity. Endogeneity arises from (1) omitted variable bias — a confounder correlated with both the regressor and the outcome, (2) reverse causality, or (3) measurement error in the regressors.

In the presence of endogeneity, OLS is biased and inconsistent. Remedies include instrumental variables (IV / 2SLS), panel fixed effects (FE), difference-in-differences (DiD), and regression discontinuity design (RDD).

OLS is also sensitive to influential observations (outliers with high leverage). A small number of such points can substantially shift coefficient estimates. Always inspect residual plots and Cook's distance.`,
  },
  ols_se_nonrobust: {
    title: "What Are Classical (Non-Robust) Standard Errors?",
    body: `Classical OLS standard errors assume homoscedasticity — that the error variance is constant across all observations: Var(uᵢ | X) = σ² (a constant). Under this assumption, the variance of β̂ is estimated by s²(X'X)⁻¹, where s² is the unbiased residual variance estimator.

When homoscedasticity holds, classical standard errors are the most efficient (smallest) among consistent estimators. If the residual-vs-fitted plot shows no fan-shaped or systematic heteroscedastic pattern, classical standard errors are appropriate.

If heteroscedasticity is present, classical standard errors are inconsistent — they can be under- or over-estimated — which distorts t-statistics and inference. In that case, use HC-robust standard errors.

$$
s^2 = \\frac{\\hat{u}'\\hat{u}}{n - k}, \\quad \\widehat{V}(\\hat{\\beta}) = s^2(X'X)^{-1}
$$

**Assumptions**

① Homoscedasticity: Var(uᵢ | X) = σ² (constant) must hold. ② Strict exogeneity and no serial correlation. ③ Diagnostic tests for homoscedasticity include the Breusch-Pagan test and White test. When these reject homoscedasticity, switch to HC-robust standard errors.`,
  },
  ols_se_robust: {
    title:
      "What Are HC-Robust (Heteroscedasticity-Consistent) Standard Errors?",
    body: `HC (Heteroscedasticity-Consistent) standard errors use a sandwich estimator — weighting each observation's squared residual ûᵢ² — to produce asymptotically valid standard errors even when the error variance is non-constant (heteroscedastic).

The OLS coefficient estimates β̂ are unchanged; only their standard errors differ. HC standard errors are recommended whenever cross-sectional data exhibit heteroscedasticity — which is common when variance tends to increase with the level of the dependent variable (e.g., income, sales).

HC0 through HC3 differ in their degree of finite-sample correction. Choosing the right variant matters particularly in small samples.

$$
\\widehat{V}_{\\mathrm{HC}}(\\hat{\\beta}) = (X'X)^{-1}\\!\\left(\\sum_{i=1}^n \\hat{u}_i^2\\, x_i x_i'\\right)\\!(X'X)^{-1}
$$

### HC0 Through HC3: Differences and Guidance

[HC0] White's original heteroscedasticity-consistent estimator. Tends to underestimate standard errors in small samples.

[HC1] HC0 multiplied by the degrees-of-freedom correction n/(n−k). Equivalent to Stata's 'robust' option and the most widely used variant in applied economics.

[HC2] Adjusts each squared residual by the observation's leverage (hat value hᵢᵢ): ûᵢ²/(1−hᵢᵢ). More conservative than HC1.

[HC3] Divides each squared residual by (1−hᵢᵢ)², giving high-leverage observations a larger upward correction. Recommended for small samples (n ≲ 250) per MacKinnon & White (1985).`,
  },
  ols_se_hac: {
    title: "What Are HAC (Newey-West) Standard Errors?",
    body: `HAC (Heteroscedasticity and Autocorrelation Consistent) standard errors are robust to both serial correlation (autocorrelation) and heteroscedasticity in the error terms. They are the standard choice for time-series data where residuals exhibit temporal dependence.

In time-series regressions, residuals uₜ are often serially correlated — today's shock is related to yesterday's (e.g., business cycles, seasonality). HC standard errors ignore this autocorrelation and understate uncertainty. HAC standard errors correct for it by applying a kernel function (e.g., Bartlett) to weight lagged autocovariance terms before summing them into the long-run variance estimator.

Newey and West (1987) is the canonical implementation. The choice of bandwidth (number of lags L) is crucial: too small leads to under-correction; too large leads to unstable estimates. Common rules of thumb are T^(1/4) or T^(1/3).

$$
\\widehat{V}_{\\mathrm{HAC}}(\\hat{\\beta}) = (X'X)^{-1}\\,\\hat{S}\\,(X'X)^{-1}, \\quad \\hat{S} = \\sum_{\\ell=-(L)}^{L} k\\!\\left(\\frac{\\ell}{L+1}\\right)\\hat{\\Gamma}_\\ell
$$

**Assumptions**

① Primarily for time-series data; not needed for pure cross-sectional data. ② (Weak) stationarity is required. ③ Bandwidth L is typically set to T^(1/4) or T^(1/3); automatic selection (e.g., Newey-West plug-in) is also available. ④ For strongly persistent series (near unit root), HAC may be insufficient — consider GLS or ARIMA-based approaches.`,
  },
  ols_se_cluster: {
    title: "What Are Clustered Standard Errors?",
    body: `Clustered standard errors allow for arbitrary within-cluster correlation of residuals — observations within the same cluster can be correlated in any way, while observations across different clusters must be independent. Typical examples: students within the same school, employees within the same firm, or observations from the same county.

They are computed as a cluster-level sandwich estimator: instead of summing individual squared residuals (as in HC), the cluster-level score vectors are aggregated first, then squared and summed across clusters. This accounts for any within-cluster dependence structure.

After panel regressions with individual or firm fixed effects, it is standard practice to cluster standard errors at the individual or firm level to account for temporal dependence within units.

$$
\\widehat{V}_{\\mathrm{cl}}(\\hat{\\beta}) = (X'X)^{-1}\\!\\left(\\sum_{g=1}^{G} X_g'\\hat{u}_g\\hat{u}_g'X_g\\right)\\!(X'X)^{-1}
$$

**Assumptions**

① Independence across clusters is required (arbitrary within-cluster correlation is permitted). ② The number of clusters G must be sufficiently large — the rule of thumb is G ≥ 50. With few clusters, standard errors are downward-biased and t-statistics are inflated. ③ When G is small (< 50), use Wild Cluster Bootstrap for inference. ④ The clustering level should match the unit at which treatment is assigned or at which correlation naturally arises.`,
  },
  wls_result_coefficients: {
    title: "How to Read the WLS Coefficient Table",
    body: `The WLS coefficient table has the same structure as OLS (coef, std err, t-stat, p-value, 95% CI), but all estimates are derived from the **weighted least-squares criterion**.

[coef (Coefficient)] The estimated change in y per unit increase in x\u2c7c, holding other predictors constant. Under correctly specified weights, these estimates are unbiased and more efficient than OLS.

[std err (Standard Error)] The WLS-based standard error. When weights are correctly specified, std err is smaller than OLS (efficiency gain). If the weights are misspecified, std err can be misleadingly small.

[t-stat / p-value / 95% CI] Interpreted the same as in OLS. A large sample approximation of coef \u00b1 1.96 \u00d7 std err is used for the 95% CI.

### WLS-Specific Cautions

**Misspecified weights introduce bias risk**: even though the coefficient is still unbiased, an incorrect variance structure leads to incorrect standard errors and invalid inference. If the variance structure is uncertain, consider adding HC robust standard errors on top of WLS.

**Weights must be strictly positive**: the specified column must contain values > 0 in every row used for estimation. Zero, negative, or missing weights will cause an API error.`,
  },
  wls_result_model_stats: {
    title: "How to Read WLS Model Statistics",
    body: `WLS model statistics follow the same layout as OLS (R\u00b2, Adjusted R\u00b2, F-stat, Log-Likelihood, Observations), but the **R\u00b2 is a \u2018weighted R\u00b2\u2019** based on the weighted residual sum of squares.

### Weighted R\u00b2

$$
R^2_{WLS} = 1 - \\frac{\\sum_i w_i (y_i - \\hat{y}_i)^2}{\\sum_i w_i (y_i - \\bar{y}_w)^2}, \\quad \\bar{y}_w = \\frac{\\sum_i w_i y_i}{\\sum_i w_i}
$$

When all weights equal 1 (i.e., OLS), this reduces to the ordinary R\u00b2. Because high-variance observations receive low weights, the weighted R\u00b2 can differ substantially from the unweighted OLS R\u00b2 on the same data.

### Other Statistics

[F-stat / F-prob] Test that all slope coefficients are jointly zero. Interpreted the same as OLS. Due to WLS efficiency gains, F values tend to be higher than OLS on the same data.

[Log-Likelihood] The maximum-likelihood value for the WLS model. Used to compute AIC/BIC for model comparison.

### Caution When Comparing WLS and OLS

Do not directly compare the WLS R\u00b2 to the OLS R\u00b2 on the same data\u2014their definitions differ. The advantage of WLS lies in **smaller coefficient standard errors (efficiency) and correct inference**, not in a higher R\u00b2.`,
  },
  // ---------------------------------------------------------------------------
  // Reading regression output
  // ---------------------------------------------------------------------------
  ols_result_coefficients: {
    title: "How to Read the Coefficient Table",
    body: `The coefficient table is the primary output of any regression analysis, showing the estimated effect and statistical reliability of each predictor.

[coef (Coefficient)] For OLS, this is the estimated change in the outcome y when predictor xⱼ increases by one unit, holding all other predictors constant (ceteris paribus). It is an associational measure unless the identification strategy supports a causal interpretation.

[std err (Standard Error)] Measures the precision of the coefficient estimate — the smaller, the more precise. Its value depends on the chosen standard error type (classical, HC, HAC, or clustered).

### t-Statistic · p-Value · 95% Confidence Interval

[t-statistic] coef ÷ std err. Measures how many standard errors the estimate lies from zero (the null hypothesis). As a rule of thumb, |t| > 2 suggests statistical significance.

[p-value] The two-tailed p-value corresponding to the t-statistic. Significance at α = 0.05 is declared when p < 0.05. Significance markers: *** p < 0.01, ** p < 0.05, * p < 0.1 (conventional notation).

[95% CI] Approximately coef ± 1.96 × std err for large samples. If the interval excludes 0, the result is significant at the 5% level. The CI conveys both the direction and the plausible range of the effect, making it more informative than the p-value alone.

### Interpreting the AME Column (Logit / Probit)

For logit and probit models, the raw coefficient measures the change in log-odds (logit) or the latent index (probit), which is not directly interpretable as a probability effect.

AME (Average Marginal Effect) evaluates the partial derivative ∂p/∂xⱼ at each observation and averages over the sample. Interpretation: 'A one-unit increase in xⱼ is associated with an average change in the probability of the outcome of AME percentage points.' For example, AME = 0.05 means the probability rises by 5 pp on average.

AME is directly comparable to the coefficient from a linear probability model (LPM). Its standard errors are computed via the delta method.`,
  },
  ols_result_model_stats: {
    title: "How to Read the Model Statistics",
    body: `Model-level statistics assess the overall fit, information content, and joint significance of the estimated model — complementing the individual coefficient tests.

[R² (R-squared)] The proportion of variance in the dependent variable explained by the model (0 to 1). Higher is better, but R² always increases when regressors are added. Use Adjusted R² for model comparisons.

[Adjusted R²] Penalizes R² for each additional regressor. If a new variable adds no real explanatory power, Adjusted R² decreases. It is the standard criterion for variable selection in OLS.

### OLS-Specific Statistics

[F-statistic / Prob(F)] Tests H₀: all slope coefficients jointly equal zero. A significant p-value (Prob(F) < 0.05) means the model as a whole has statistically significant predictive power. If F is not significant but individual t-stats are, suspect multicollinearity.

[AIC (Akaike Information Criterion) / BIC (Bayesian Information Criterion)] Information criteria that penalize model complexity — lower is better. Used to compare models on the same dataset (absolute values are not meaningful; compare differences). BIC imposes a heavier penalty than AIC and tends to favor more parsimonious models.

[Log-Likelihood] The maximum likelihood value achieved by the model. Used to compute AIC and BIC; higher (less negative) values indicate better fit.

### Logit / Probit-Specific Statistics

[Pseudo-R² (McFadden's)] 1 − log L_full / log L_null. Analogous to R² in OLS but not directly comparable. Values of 0.2–0.4 are considered a good fit; do not interpret them the same way as OLS R².

[Log-Likelihood (Null)] The log-likelihood of the intercept-only model (baseline). Serves as the reference point for measuring improvement from adding regressors.

[LR Statistic (Likelihood Ratio)] −2 × (log L_null − log L_full). Follows a chi-squared distribution with degrees of freedom equal to the number of regressors. Tests whether all slope coefficients are jointly zero — the MLE analog of the F-test.`,
  },
  // ---------------------------------------------------------------------------
  // Discrete choice models
  // ---------------------------------------------------------------------------
  logit_model: {
    title: "What Is the Logit Model?",
    body: `The logit model (logistic regression) is the standard approach when the outcome variable is binary (0 or 1). Fitting OLS to a binary outcome (the Linear Probability Model) can yield predicted probabilities outside [0,1], which is theoretically incoherent. The logit model passes the linear index Xβ through the logistic function, guaranteeing predicted probabilities in (0,1).

The logit model assumes that the log-odds (logit) of the probability is linear in the predictors: log(p/(1−p)) = Xβ, which rearranges to p = 1/(1+e^(−Xβ)) — the sigmoid/logistic function.

Parameters are estimated by maximum likelihood (MLE). Unlike OLS, there is no closed-form solution; numerical optimization (e.g., Newton-Raphson) is required.

$$
\\log\\frac{p}{1-p} = X\\beta \\implies p = \\frac{1}{1+e^{-X\\beta}}
$$

### Comparison with the Linear Probability Model (LPM)

[LPM (OLS on a binary outcome)] Coefficients are directly interpretable as probability changes and are compatible with robust standard errors and fixed effects. However, predicted probabilities can exceed [0,1] and error terms are necessarily heteroscedastic.

[Logit] Predicted probabilities always lie in (0,1). The direct coefficient interpretation (log-odds / odds ratio) is non-intuitive for most audiences, so Average Marginal Effects (AME) are the standard reporting metric. Logit is particularly valuable when observations cluster near probability 0 or 1.

### Coefficient Interpretation · AME · Pseudo-R²

[Direct coefficient] βⱼ measures the change in log-odds when xⱼ increases by one unit. The exponentiated coefficient exp(βⱼ) is the odds ratio.

[AME (Average Marginal Effect)] The sample average of ∂p/∂xⱼ = p(1−p)βⱼ evaluated at each observation. AME represents 'the average change in the predicted probability of the outcome when xⱼ increases by one unit,' directly comparable to LPM coefficients.

[McFadden's Pseudo-R²] 1 − log L_full / log L_null. A value of 0.2–0.4 generally indicates a good fit — but do not compare it numerically to OLS R².`,
  },
  probit_model: {
    title: "What Is the Probit Model?",
    body: `The probit model is the second standard approach (alongside logit) for binary outcome variables. Where logit uses the cumulative logistic distribution, probit uses the standard normal CDF, Φ: p = Φ(Xβ).

The probit model can be derived from a latent-variable framework: yᵢ* = Xβ + εᵢ where εᵢ ~ N(0,1). The observed outcome yᵢ = 1 if and only if yᵢ* > 0. The normality assumption on ε distinguishes probit from logit (which assumes a logistic error distribution).

In practice, logit and probit produce nearly identical results: coefficient ratios, predicted probabilities, and AME values are very close. Logit tends to be preferred for its closed-form log-likelihood and the ease of interpreting odds ratios.

$$
p = \\Phi(X\\beta), \\quad \\Phi(z) = \\int_{-\\infty}^{z} \\frac{1}{\\sqrt{2\\pi}}e^{-t^2/2}\\,dt
$$

### Differences from Logit and When to Use Probit

[Tail behavior] Probit assumes normal tails, which decay faster than logistic tails. In practice the difference is negligible for most datasets.

[Heckman selection model] Probit is the standard first-stage specification in Heckman's two-step selection correction (Heckman, 1979). When sample selection bias is a concern — because the outcome is only observed for a non-random subset — the Heckman estimator uses a probit selection equation to compute the inverse Mills ratio, which is then included in the outcome equation to correct for selection bias.

### AME Interpretation and Choosing Among LPM, Logit, and Probit

[AME (Average Marginal Effect)] The sample average of ∂p/∂xⱼ = φ(Xᵢβ)βⱼ, where φ is the standard normal PDF. Interpretation is the same as in logit: 'a one-unit increase in xⱼ is associated with an average change in the probability of AME percentage points.'

[Choosing among LPM, Logit, and Probit] LPM offers the simplest coefficient interpretation and straightforward compatibility with fixed effects and robust standard errors. Logit/Probit ensure predicted probabilities stay within (0,1) but require reporting AME. In causal inference contexts where the focus is on the average effect rather than distributional fit, LPM is often preferred for its transparency.`,
  },
  iv_method: {
    title: "What Is the Instrumental Variables (IV / 2SLS) Method?",
    size: "lg",
    body: `Instrumental Variables (IV) estimation is used when explanatory variables are **endogenous** — correlated with the error term. Endogeneity arises from ① omitted variable bias, ② reverse causality, or ③ measurement error, all of which make OLS biased and inconsistent.

An instrument z must satisfy two conditions:

**① Relevance**: z is correlated with the endogenous regressor x (E[z'x] ≠ 0)
**② Exogeneity / Exclusion Restriction**: z affects y only through x, not directly (E[z'u] = 0)

### How 2SLS Works

**Two-Stage Least Squares (2SLS)** is the most widely used IV estimator.

**First stage**: Regress the endogenous variable x on instruments z to obtain fitted values $\\hat{x}$.

$$\\hat{x} = Z(Z'Z)^{-1}Z'x$$

**Second stage**: Replace x with $\\hat{x}$ in the structural equation and estimate by OLS.

$$\\hat{\\beta}_{2SLS} = (\\hat{X}'\\hat{X})^{-1}\\hat{X}'y$$

The key idea: the first stage extracts only the exogenous variation in x (driven by z), purging the endogenous part. The 2SLS estimator is consistent in large samples (though biased in finite samples).

### Identification Conditions

| Condition | # Instruments | Result |
|---|---|---|
| Under-identified | \\|Z\\| < \\|X_{endog}\\| | Not estimable |
| Exactly identified | \\|Z\\| = \\|X_{endog}\\| | 2SLS only |
| Over-identified | \\|Z\\| > \\|X_{endog}\\| | 2SLS or GMM valid |

**This app requires the number of instruments ≥ number of endogenous variables.**

### The Weak Instruments Problem

When instruments are only weakly correlated with the endogenous regressor, 2SLS can be severely biased and unstable in finite samples.

The standard diagnostic is the **first-stage F-statistic**. A common rule of thumb is **F > 10** (Stock & Yogo, 2005) as evidence of strong instruments. This value is included in the analysis results.

If the F-statistic is low, reconsider your choice of instruments. Weak instruments can produce estimates worse than OLS.

### 2SLS vs. GMM

**2SLS** assumes homoskedastic errors and is efficient under that assumption. It works well for exactly-identified or over-identified models with homoskedastic errors.

**GMM (Generalized Method of Moments)** uses a weighting matrix to optimally combine the moment conditions and is more efficient than 2SLS when errors are heteroskedastic and the model is over-identified. However, GMM has poorer finite-sample properties in small samples.

Intuitively, GMM "optimally weights the information from multiple instruments." When in doubt, start with 2SLS.

### ⚠️ Risk of Omitting the Constant

Dropping the constant term risks violating the exogeneity condition E[z'u] = 0 by absorbing the intercept into the error term. Unless you have a specific theoretical justification, **always include the constant**.`,
  },
} satisfies ExplainerContentMap;

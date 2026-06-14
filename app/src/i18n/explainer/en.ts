import type { ExplainerContentMap } from "./types";

export const enExplainer = {
  confidence_interval: {
    title: "What Is a Confidence Interval?",
    description:
      'A confidence interval gives you an upper and lower bound for an estimated value. Typically, 90%, 95%, or 99% intervals are used.\n\nWhen you hear "95% confidence interval", it\'s tempting to think "there is a 95% probability that the true value lies within this interval" — but this is incorrect. In frequentist statistics, the true value is a single fixed number. What varies is the confidence interval itself (both its upper and lower bounds) calculated from our data.\n\nThe correct interpretation: "If we repeated this with 100 independent datasets, approximately 95 of the resulting intervals would contain the true fixed value." This is the meaning of a 95% confidence interval.',
    sections: [
      {
        heading: "Why use the distribution of the estimator?",
        body: 'The width of a confidence interval is not determined by the spread of the raw data, but by the sampling distribution — how the estimated mean or coefficient would vary across hypothetical repeated samples.\n\nAs sample size increases, estimated values cluster more tightly around the true value. We use this "spread of the estimator (standard error)" to determine the interval width.',
      },
      {
        heading: "Why the estimator follows a bell-shaped distribution",
        body: "On the shape of the estimator's distribution:\n\nSmall samples (n), data approximately normal: By the Student-Fisher theorem, the standardized estimator follows a t-distribution (a bell curve with slightly heavier tails) exactly. This is a mathematical result derived from the normality assumption — not the Central Limit Theorem. Note: for small samples with non-normal data, the t-distribution may not be appropriate.\n\nLarge samples (n): Regardless of how skewed the raw data is, the Central Limit Theorem tells us that the estimator's distribution converges toward a normal (Gaussian) bell curve. Note that \"large enough\" depends on the shape of the data distribution.\n\nBecause the estimator distribution becomes bell-shaped, we can calculate the exact interval width that will capture the true value approximately 95% of the time.",
      },
      {
        heading: "Connection to hypothesis tests, t-values and p-values",
        body: 'The confidence interval framework is the flip side of hypothesis testing, t-values, and p-values.\n\nHypothesis testing asks: "Is the effect of this variable truly zero?" (null hypothesis).\n\nIf the 95% confidence interval does not contain 0, the estimated value is far enough from zero that the interval cannot capture it. In this case:\n\u2022 p-value \u2264 0.05 (5%)\n\u2022 |t-value| \u2265 1.96 for large samples (normal approximation), or \u2265 degrees-of-freedom-dependent critical value (typically > 2) for small samples (t-distribution)\n\nConclusion: "The effect is statistically significant (we cannot claim it is zero)."',
      },
    ],
  },
  mean: {
    title: "Confidence Interval for the Mean (t-distribution)",
    description:
      "Computes a confidence interval for the population mean μ using the sample mean x̄ as a point estimate. Applies when data come from a normal distribution or the sample size is large (central limit theorem).",
    formula: "\\bar{x} \\pm t_{\\alpha/2,\\, n-1} \\cdot \\frac{s}{\\sqrt{n}}",
    assumptions:
      "Data are i.i.d. (independently and identically distributed). For small samples the distribution should be approximately normal.",
  },
  median: {
    title: "Confidence Interval for the Median (Bootstrap)",
    description:
      "Estimates the confidence interval for the median using the Bootstrap method (1,000 resamples). This is a non-parametric approach that requires no distributional assumptions.",
    formula:
      "\\left[\\hat{m}^*_{(\\alpha/2)},\\;\\hat{m}^*_{(1-\\alpha/2)}\\right]",
    assumptions:
      "Data should be a representative sample of the population. Accuracy decreases for very small samples.",
  },
  proportion: {
    title: "Confidence Interval for a Proportion (Wilson Score)",
    description:
      "Computes the Wilson score interval for the success proportion p̂ of binary data (0 or 1 only). Outperforms the Wald interval in small-sample coverage. The column must contain only 0 and 1 values.",
    formula:
      "\\frac{\\hat{p} + \\dfrac{z^2}{2n} \\pm z\\sqrt{\\dfrac{\\hat{p}(1-\\hat{p})}{n} + \\dfrac{z^2}{4n^2}}}{1 + \\dfrac{z^2}{n}}",
    assumptions:
      "Column values must be binary (0 or 1 only). The API will return an error if other values are present.",
  },
  variance: {
    title: "Confidence Interval for the Variance (Chi-squared)",
    description:
      "Computes a confidence interval for the population variance σ² using the sample variance s² and the chi-squared distribution. Exact when data are normally distributed.",
    formula:
      "\\left[\\frac{(n-1)s^2}{\\chi^2_{\\alpha/2,\\, n-1}},\\;\\frac{(n-1)s^2}{\\chi^2_{1-\\alpha/2,\\, n-1}}\\right]",
    assumptions:
      "Data must be normally distributed. Coverage degrades when the normality assumption is violated.",
  },
  standard_deviation: {
    title: "Confidence Interval for the Standard Deviation",
    description:
      "Derives the confidence interval for the standard deviation σ as the square root of the variance CI bounds. The same normality assumption as the variance CI applies.",
    formula:
      "\\left[\\sqrt{\\text{CI}_{\\text{lower}}(\\sigma^2)},\\;\\sqrt{\\text{CI}_{\\text{upper}}(\\sigma^2)}\\right]",
    assumptions:
      "Data must be normally distributed (same as the variance CI assumption).",
  },
} satisfies ExplainerContentMap;

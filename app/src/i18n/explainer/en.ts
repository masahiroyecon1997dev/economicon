import type { ExplainerContentMap } from "./types";

export const enExplainer = {
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

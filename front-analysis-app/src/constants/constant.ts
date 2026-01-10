import type { DistributionType } from "../types/commonTypes";

export const HEADER_MENU_HEIGHT = 40;
export const TABLE_TAB_HEIGHT = 40;
export const CSV_SEPARATORS = [","];

export const DISTRIBUTION_OPTIONS: Array<{
  value: DistributionType;
  label: string;
  params: string[];
}> = [
  {
    value: "uniform",
    label: "Common.UniformDistribution",
    params: ["low", "high"],
  },
  {
    value: "normal",
    label: "Common.NomalDistribution",
    params: ["mean", "deviation"],
  },
  {
    value: "exponential",
    label: "Common.ExponentialDistribution",
    params: ["rate"],
  },
  {
    value: "gamma",
    label: "Common.GammaDistribution",
    params: ["shape", "scale"],
  },
  {
    value: "beta",
    label: "Common.BetaDistribution",
    params: ["alpha", "beta"],
  },
  {
    value: "weibull",
    label: "Common.WeibullDistribution",
    params: ["shape", "scale"],
  },
  {
    value: "lognormal",
    label: "Common.LognormalDistribution",
    params: ["logMean", "logSD"],
  },
  {
    value: "binomial",
    label: "Common.BinomialDistribution",
    params: ["trials", "probability"],
  },
  {
    value: "bernoulli",
    label: "Common.BernoulliDistribution",
    params: ["probability"],
  },
  { value: "poisson", label: "Common.PoissonDistribution", params: ["lambda"] },
  {
    value: "geometric",
    label: "Common.GeometricDistribution",
    params: ["probability"],
  },
  {
    value: "hypergeometric",
    label: "Common.HypergeometricDistribution",
    params: ["populationSize", "numberOfSuccesses", "sampleSize"],
  },
];

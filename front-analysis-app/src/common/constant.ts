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
    params: ["loc", "scale"],
  },
  {
    value: "exponential",
    label: "Common.ExponentialDistribution",
    params: ["scale"],
  },
  {
    value: "gamma",
    label: "Common.GammaDistribution",
    params: ["shape", "scale"],
  },
  { value: "beta", label: "Common.BetaDistribution", params: ["a", "b"] },
  { value: "weibull", label: "Common.WeibullDistribution", params: ["a"] },
  {
    value: "lognormal",
    label: "Common.LognormalDistribution",
    params: ["mean", "sigma"],
  },
  {
    value: "binomial",
    label: "Common.BinomialDistribution",
    params: ["n", "p"],
  },
  { value: "bernoulli", label: "Common.BernoulliDistribution", params: ["p"] },
  { value: "poisson", label: "Common.PoissonDistribution", params: ["lam"] },
  { value: "geometric", label: "Common.GeometricDistribution", params: ["p"] },
  {
    value: "hypergeometric",
    label: "Common.HypergeometricDistribution",
    params: ["K", "N", "n"],
  },
];

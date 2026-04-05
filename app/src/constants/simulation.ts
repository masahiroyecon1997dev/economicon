/**
 * シミュレーション分布に関する共通定数・スキーマ・ヘルパー
 *
 * AddSimulationColumnForm / SimulationColumnConfig の両方で使用する。
 * パラメータ名は API 直接名（loc, scale, n, p など）で統一。
 */
import { z } from "zod";
import type { DistributionType } from "../types/commonTypes";

/** 連続分布タイプ */
export const CONTINUOUS_DIST_TYPES: DistributionType[] = [
  "uniform",
  "exponential",
  "normal",
  "gamma",
  "beta",
  "weibull",
  "lognormal",
];

/** 離散分布タイプ */
export const DISCRETE_DIST_TYPES: DistributionType[] = [
  "binomial",
  "bernoulli",
  "poisson",
  "geometric",
  "hypergeometric",
  "negative_binomial",
];

/** すべての分布タイプ（表示順） */
export const DIST_TYPES: DistributionType[] = [
  "uniform",
  "exponential",
  "normal",
  "gamma",
  "beta",
  "weibull",
  "lognormal",
  "binomial",
  "bernoulli",
  "poisson",
  "geometric",
  "hypergeometric",
  "negative_binomial",
  "fixed",
];

/** 各分布で使用するパラメータ名（API 直接名） */
export const DIST_PARAMS: Record<DistributionType, string[]> = {
  uniform: ["low", "high"],
  exponential: ["scale"],
  normal: ["loc", "scale"],
  gamma: ["shape", "scale"],
  beta: ["a", "b"],
  weibull: ["a", "scale"],
  lognormal: ["mean", "sigma"],
  binomial: ["n", "p"],
  bernoulli: ["p"],
  poisson: ["lam"],
  geometric: ["p"],
  hypergeometric: ["populationSize", "successCount", "sampleSize"],
  negative_binomial: ["n", "p"],
  fixed: ["value"],
};

/** パラメータの i18n キー */
export const DIST_PARAM_LABEL_KEYS: Record<string, string> = {
  low: "AddSimulationColumnForm.Low",
  high: "AddSimulationColumnForm.High",
  scale: "AddSimulationColumnForm.Scale",
  loc: "AddSimulationColumnForm.Loc",
  shape: "AddSimulationColumnForm.Shape",
  a: "AddSimulationColumnForm.A",
  b: "AddSimulationColumnForm.B",
  mean: "AddSimulationColumnForm.Mean",
  sigma: "AddSimulationColumnForm.Sigma",
  n: "AddSimulationColumnForm.N",
  p: "AddSimulationColumnForm.P",
  lam: "AddSimulationColumnForm.Lam",
  populationSize: "AddSimulationColumnForm.PopulationSize",
  successCount: "AddSimulationColumnForm.SuccessCount",
  sampleSize: "AddSimulationColumnForm.SampleSize",
  value: "AddSimulationColumnForm.Value",
};

/** 各分布のデフォルトパラメータ値 */
export const DIST_PARAM_DEFAULTS: Record<
  DistributionType,
  Record<string, number>
> = {
  uniform: { low: 0, high: 10 },
  exponential: { scale: 1 },
  normal: { loc: 0, scale: 1 },
  gamma: { shape: 2, scale: 1 },
  beta: { a: 2, b: 2 },
  weibull: { a: 1, scale: 1 },
  lognormal: { mean: 0, sigma: 1 },
  binomial: { n: 10, p: 0.5 },
  bernoulli: { p: 0.5 },
  poisson: { lam: 1 },
  geometric: { p: 0.5 },
  hypergeometric: { populationSize: 20, successCount: 5, sampleSize: 10 },
  negative_binomial: { n: 5, p: 0.5 },
  fixed: { value: 0 },
};

// ── Zod スキーマファクトリ（文字列入力用） ──────────────────────────────────

const gtZeroNum = () =>
  z
    .string()
    .refine(
      (v) => !isNaN(Number(v)) && Number(v) > 0,
      "0 より大きい数値を入力してください。",
    );

const probability = () =>
  z
    .string()
    .refine(
      (v) => !isNaN(Number(v)) && Number(v) > 0 && Number(v) <= 1,
      "0 を超え 1 以下の数値を入力してください。",
    );

const anyNum = () =>
  z.string().refine((v) => !isNaN(Number(v)), "数値を入力してください。");

const gtZeroInt = () =>
  z
    .string()
    .refine(
      (v) => !isNaN(Number(v)) && Number(v) > 0 && Number.isInteger(Number(v)),
      "1 以上の整数を入力してください。",
    );

/** パラメータ別 Zod スキーマ（string 入力バリデーション用） */
export const DIST_PARAM_SCHEMAS: Record<string, () => z.ZodTypeAny> = {
  low: anyNum,
  high: anyNum,
  scale: gtZeroNum,
  loc: anyNum,
  shape: gtZeroNum,
  a: gtZeroNum,
  b: gtZeroNum,
  mean: anyNum,
  sigma: gtZeroNum,
  n: gtZeroInt,
  p: probability,
  lam: gtZeroNum,
  populationSize: gtZeroInt,
  successCount: gtZeroInt,
  sampleSize: gtZeroInt,
  value: anyNum,
};

/** API リクエスト用分布オブジェクトを組み立てる */
export const buildDistributionFromParams = (
  type: DistributionType,
  params: Record<string, number>,
) => {
  switch (type) {
    case "uniform":
      return { type, low: params.low, high: params.high };
    case "exponential":
      return { type, scale: params.scale };
    case "normal":
      return { type, loc: params.loc, scale: params.scale };
    case "gamma":
      return { type, shape: params.shape, scale: params.scale };
    case "beta":
      return { type, a: params.a, b: params.b };
    case "weibull":
      return { type, a: params.a, scale: params.scale };
    case "lognormal":
      return { type, mean: params.mean, sigma: params.sigma };
    case "binomial":
      return { type, n: params.n, p: params.p };
    case "bernoulli":
      return { type, p: params.p };
    case "poisson":
      return { type, lam: params.lam };
    case "geometric":
      return { type, p: params.p };
    case "hypergeometric":
      return {
        type,
        populationSize: params.populationSize,
        successCount: params.successCount,
        sampleSize: params.sampleSize,
      };
    case "negative_binomial":
      return { type, n: params.n, p: params.p };
    case "fixed":
      return { type, value: params.value };
  }
};

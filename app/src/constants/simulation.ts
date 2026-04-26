/**
 * シミュレーション分布に関する共通定数・スキーマ・ヘルパー
 *
 * AddSimulationColumnForm / SimulationColumnConfig の両方で使用する。
 * パラメータ名は API 直接名（loc, scale, n, p など）で統一。
 */
import type { DistributionType } from "@/types/commonTypes";
import { z } from "zod";

export type DistributionCategory = "continuous" | "discrete" | "deterministic";

type DistributionDefinition = {
  value: DistributionType;
  category: DistributionCategory;
  params: string[];
};

const DISTRIBUTION_DEFINITIONS: DistributionDefinition[] = [
  {
    value: "uniform",
    category: "continuous",
    params: ["low", "high"],
  },
  {
    value: "exponential",
    category: "continuous",
    params: ["scale"],
  },
  {
    value: "normal",
    category: "continuous",
    params: ["loc", "scale"],
  },
  {
    value: "gamma",
    category: "continuous",
    params: ["shape", "scale"],
  },
  {
    value: "beta",
    category: "continuous",
    params: ["a", "b"],
  },
  {
    value: "weibull",
    category: "continuous",
    params: ["a", "scale"],
  },
  {
    value: "lognormal",
    category: "continuous",
    params: ["mean", "sigma"],
  },
  {
    value: "binomial",
    category: "discrete",
    params: ["n", "p"],
  },
  {
    value: "bernoulli",
    category: "discrete",
    params: ["p"],
  },
  {
    value: "poisson",
    category: "discrete",
    params: ["lam"],
  },
  {
    value: "geometric",
    category: "discrete",
    params: ["p"],
  },
  {
    value: "hypergeometric",
    category: "discrete",
    params: ["populationSize", "successCount", "sampleSize"],
  },
  {
    value: "negative_binomial",
    category: "discrete",
    params: ["n", "p"],
  },
  {
    value: "sequence",
    category: "deterministic",
    params: ["start", "step"],
  },
  {
    value: "fixed",
    category: "deterministic",
    params: ["value"],
  },
];

const getDistributionTypesByCategory = (
  category: DistributionCategory,
): DistributionType[] =>
  DISTRIBUTION_DEFINITIONS.filter(
    (definition) => definition.category === category,
  ).map((definition) => definition.value);

/** 連続分布タイプ */
export const CONTINUOUS_DIST_TYPES =
  getDistributionTypesByCategory("continuous");

/** 離散分布タイプ */
export const DISCRETE_DIST_TYPES = getDistributionTypesByCategory("discrete");

/** 決定的系列タイプ */
export const DETERMINISTIC_DIST_TYPES =
  getDistributionTypesByCategory("deterministic");

export const getDistributionCategory = (
  distributionType: DistributionType,
): DistributionCategory =>
  DISTRIBUTION_DEFINITIONS.find(
    (definition) => definition.value === distributionType,
  )?.category ?? "continuous";

/** すべての分布タイプ（表示順） */
export const DIST_TYPES = DISTRIBUTION_DEFINITIONS.map(
  (definition) => definition.value,
);

/** 各分布で使用するパラメータ名（API 直接名） */
export const DIST_PARAMS = Object.fromEntries(
  DISTRIBUTION_DEFINITIONS.map((definition) => [
    definition.value,
    definition.params,
  ]),
) as Record<DistributionType, string[]>;

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
  start: "AddSimulationColumnForm.Start",
  step: "AddSimulationColumnForm.Step",
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
  sequence: { start: 1, step: 1 },
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
  start: anyNum,
  step: anyNum,
  value: anyNum,
};

/** API リクエスト用分布オブジェクトを組み立てる */
export const buildDistributionFromParams = (
  type: DistributionType,
  params: Record<string, number>,
) =>
  Object.assign(
    { type },
    Object.fromEntries(
      DIST_PARAMS[type].map((param) => [param, params[param]]),
    ),
  );

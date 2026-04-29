/**
 * シミュレーション分布に関する共通定数・スキーマ・ヘルパー
 *
 * AddSimulationColumnForm / SimulationColumnConfig の両方で使用する。
 * パラメータ名は API の公開名（camelCase）で統一。
 */
import type { DistributionConfig } from "@/api/model";
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
    params: ["scaleParameter"],
  },
  {
    value: "normal",
    category: "continuous",
    params: ["mean", "standardDeviation"],
  },
  {
    value: "gamma",
    category: "continuous",
    params: ["shapeParameter", "scaleParameter"],
  },
  {
    value: "beta",
    category: "continuous",
    params: ["alpha", "beta"],
  },
  {
    value: "weibull",
    category: "continuous",
    params: ["shapeParameter", "scaleParameter"],
  },
  {
    value: "lognormal",
    category: "continuous",
    params: ["logMean", "logStandardDeviation"],
  },
  {
    value: "binomial",
    category: "discrete",
    params: ["trialCount", "successProbability"],
  },
  {
    value: "bernoulli",
    category: "discrete",
    params: ["successProbability"],
  },
  {
    value: "poisson",
    category: "discrete",
    params: ["rate"],
  },
  {
    value: "geometric",
    category: "discrete",
    params: ["successProbability"],
  },
  {
    value: "hypergeometric",
    category: "discrete",
    params: ["populationSize", "successCount", "sampleSize"],
  },
  {
    value: "negative_binomial",
    category: "discrete",
    params: ["targetSuccessCount", "successProbability"],
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

/** 各分布で使用するパラメータ名（API 公開名） */
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
  scaleParameter: "AddSimulationColumnForm.ScaleParameter",
  mean: "AddSimulationColumnForm.Mean",
  standardDeviation: "AddSimulationColumnForm.StandardDeviation",
  shapeParameter: "AddSimulationColumnForm.ShapeParameter",
  alpha: "AddSimulationColumnForm.Alpha",
  beta: "AddSimulationColumnForm.Beta",
  logMean: "AddSimulationColumnForm.LogMean",
  logStandardDeviation: "AddSimulationColumnForm.LogStandardDeviation",
  trialCount: "AddSimulationColumnForm.TrialCount",
  successProbability: "AddSimulationColumnForm.SuccessProbability",
  rate: "AddSimulationColumnForm.Rate",
  populationSize: "AddSimulationColumnForm.PopulationSize",
  successCount: "AddSimulationColumnForm.SuccessCount",
  sampleSize: "AddSimulationColumnForm.SampleSize",
  targetSuccessCount: "AddSimulationColumnForm.TargetSuccessCount",
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
  exponential: { scaleParameter: 1 },
  normal: { mean: 0, standardDeviation: 1 },
  gamma: { shapeParameter: 2, scaleParameter: 1 },
  beta: { alpha: 2, beta: 2 },
  weibull: { shapeParameter: 1, scaleParameter: 1 },
  lognormal: { logMean: 0, logStandardDeviation: 1 },
  binomial: { trialCount: 10, successProbability: 0.5 },
  bernoulli: { successProbability: 0.5 },
  poisson: { rate: 1 },
  geometric: { successProbability: 0.5 },
  hypergeometric: { populationSize: 20, successCount: 5, sampleSize: 10 },
  negative_binomial: { targetSuccessCount: 5, successProbability: 0.5 },
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
  scaleParameter: gtZeroNum,
  mean: anyNum,
  standardDeviation: gtZeroNum,
  shapeParameter: gtZeroNum,
  alpha: gtZeroNum,
  beta: gtZeroNum,
  logMean: anyNum,
  logStandardDeviation: gtZeroNum,
  trialCount: gtZeroInt,
  successProbability: probability,
  rate: gtZeroNum,
  populationSize: gtZeroInt,
  successCount: gtZeroInt,
  sampleSize: gtZeroInt,
  targetSuccessCount: gtZeroInt,
  start: anyNum,
  step: anyNum,
  value: anyNum,
};

type DistributionByType<T extends DistributionType> = Extract<
  DistributionConfig,
  { type: T }
>;

type DistributionBuilderMap = {
  [K in DistributionType]: (
    params: Record<string, number>,
  ) => DistributionByType<K>;
};

const DISTRIBUTION_BUILDERS = {
  uniform: (params) => ({
    type: "uniform",
    low: params.low,
    high: params.high,
  }),
  exponential: (params) => ({
    type: "exponential",
    scaleParameter: params.scaleParameter,
  }),
  normal: (params) => ({
    type: "normal",
    mean: params.mean,
    standardDeviation: params.standardDeviation,
  }),
  gamma: (params) => ({
    type: "gamma",
    shapeParameter: params.shapeParameter,
    scaleParameter: params.scaleParameter,
  }),
  beta: (params) => ({
    type: "beta",
    alpha: params.alpha,
    beta: params.beta,
  }),
  weibull: (params) => ({
    type: "weibull",
    shapeParameter: params.shapeParameter,
    scaleParameter: params.scaleParameter,
  }),
  lognormal: (params) => ({
    type: "lognormal",
    logMean: params.logMean,
    logStandardDeviation: params.logStandardDeviation,
  }),
  binomial: (params) => ({
    type: "binomial",
    trialCount: params.trialCount,
    successProbability: params.successProbability,
  }),
  bernoulli: (params) => ({
    type: "bernoulli",
    successProbability: params.successProbability,
  }),
  poisson: (params) => ({
    type: "poisson",
    rate: params.rate,
  }),
  geometric: (params) => ({
    type: "geometric",
    successProbability: params.successProbability,
  }),
  hypergeometric: (params) => ({
    type: "hypergeometric",
    populationSize: params.populationSize,
    successCount: params.successCount,
    sampleSize: params.sampleSize,
  }),
  negative_binomial: (params) => ({
    type: "negative_binomial",
    targetSuccessCount: params.targetSuccessCount,
    successProbability: params.successProbability,
  }),
  sequence: (params) => ({
    type: "sequence",
    start: params.start,
    step: params.step,
  }),
  fixed: (params) => ({
    type: "fixed",
    value: params.value,
  }),
} satisfies DistributionBuilderMap;

/** API リクエスト用分布オブジェクトを組み立てる */
export const buildDistributionFromParams = <T extends DistributionType>(
  type: T,
  params: Record<string, number>,
): DistributionByType<T> =>
  DISTRIBUTION_BUILDERS[type](params) as DistributionByType<T>;

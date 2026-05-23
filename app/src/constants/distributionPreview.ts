/**
 * 分布プレビュー用スライダー定数
 *
 * 各パラメータのスライダー範囲・デフォルト値・ステップを定義する。
 * DistributionPreview コンポーネント専用。simulation.ts とは分離して管理する。
 *
 * ★ hypergeometric の successCount / sampleSize の max は静的最大値（200）を設定し、
 *    実際の動的上限は DistributionPreview コンポーネント側で populationSize の
 *    現在値に追従させる。
 */
import type { DistributionType } from "@/types/commonTypes";

export type ParamRange = {
  min: number;
  max: number;
  default: number;
  step: number;
};

/**
 * 分布プレビュー用パラメータ範囲定義
 *
 * キー: API 公開名（camelCase）
 */
export const DIST_PREVIEW_PARAM_RANGES: Partial<
  Record<DistributionType, Record<string, ParamRange>>
> = {
  // ── 連続分布 ────────────────────────────────────────
  uniform: {
    low: { min: -10, max: 10, default: 0, step: 0.1 },
    high: { min: -10, max: 10, default: 1, step: 0.1 },
  },
  exponential: {
    scaleParameter: { min: 0.1, max: 10, default: 1, step: 0.1 },
  },
  normal: {
    mean: { min: -10, max: 10, default: 0, step: 0.1 },
    standardDeviation: { min: 0.1, max: 5, default: 1, step: 0.1 },
  },
  gamma: {
    shapeParameter: { min: 0.1, max: 10, default: 2, step: 0.1 },
    scaleParameter: { min: 0.1, max: 10, default: 1, step: 0.1 },
  },
  beta: {
    alpha: { min: 0.1, max: 10, default: 2, step: 0.1 },
    beta: { min: 0.1, max: 10, default: 5, step: 0.1 },
  },
  weibull: {
    shapeParameter: { min: 0.1, max: 10, default: 1.5, step: 0.1 },
    scaleParameter: { min: 0.1, max: 10, default: 1, step: 0.1 },
  },
  lognormal: {
    logMean: { min: -3, max: 3, default: 0, step: 0.1 },
    logStandardDeviation: { min: 0.1, max: 3, default: 1, step: 0.1 },
  },
  chi_square: {
    degreesOfFreedom: { min: 1, max: 30, default: 5, step: 1 },
  },
  f_distribution: {
    numeratorDf: { min: 1, max: 50, default: 5, step: 1 },
    denominatorDf: { min: 1, max: 100, default: 10, step: 1 },
  },
  // ── 離散分布 ────────────────────────────────────────
  binomial: {
    trialCount: { min: 1, max: 100, default: 10, step: 1 },
    successProbability: { min: 0.01, max: 0.99, default: 0.5, step: 0.01 },
  },
  bernoulli: {
    successProbability: { min: 0.01, max: 0.99, default: 0.5, step: 0.01 },
  },
  poisson: {
    rate: { min: 0.1, max: 30, default: 5, step: 0.1 },
  },
  geometric: {
    successProbability: { min: 0.01, max: 0.99, default: 0.3, step: 0.01 },
  },
  hypergeometric: {
    populationSize: { min: 10, max: 200, default: 50, step: 1 },
    // successCount / sampleSize の max は DistributionPreview 側で populationSize に動的追従
    successCount: { min: 1, max: 200, default: 20, step: 1 },
    sampleSize: { min: 1, max: 200, default: 10, step: 1 },
  },
  negative_binomial: {
    targetSuccessCount: { min: 1, max: 50, default: 5, step: 1 },
    successProbability: { min: 0.01, max: 0.99, default: 0.5, step: 0.01 },
  },
};

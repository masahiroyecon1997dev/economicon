import {
  buildDistributionFromParams,
  CONTINUOUS_DIST_TYPES,
  DETERMINISTIC_DIST_TYPES,
  DISCRETE_DIST_TYPES,
  DIST_PARAM_DEFAULTS,
  DIST_PARAM_LABEL_KEYS,
  DIST_PARAM_SCHEMAS,
  DIST_PARAMS,
  DIST_TYPES,
} from "@/constants/simulation";
import type { DistributionType } from "@/types/commonTypes";
import { describe, expect, it } from "vitest";

// ---------------------------------------------------------------------------
// 分布タイプ定数
// ---------------------------------------------------------------------------
describe("CONTINUOUS_DIST_TYPES", () => {
  it("test_continuousDistTypes_containsExpectedTypes", () => {
    const expected: DistributionType[] = [
      "uniform",
      "exponential",
      "normal",
      "gamma",
      "beta",
      "weibull",
      "lognormal",
    ];
    expect(CONTINUOUS_DIST_TYPES).toEqual(expected);
  });
});

describe("DISCRETE_DIST_TYPES", () => {
  it("test_discreteDistTypes_containsExpectedTypes", () => {
    const expected: DistributionType[] = [
      "binomial",
      "bernoulli",
      "poisson",
      "geometric",
      "hypergeometric",
      "negative_binomial",
    ];
    expect(DISCRETE_DIST_TYPES).toEqual(expected);
  });
});

describe("DIST_TYPES", () => {
  it("test_distTypes_containsAllContinuousAndDiscrete", () => {
    for (const t of CONTINUOUS_DIST_TYPES) {
      expect(DIST_TYPES).toContain(t);
    }
    for (const t of DISCRETE_DIST_TYPES) {
      expect(DIST_TYPES).toContain(t);
    }
  });

  it("test_distTypes_includesDeterministicTypes", () => {
    expect(DIST_TYPES).toContain("fixed");
    expect(DIST_TYPES).toContain("sequence");
  });
});

describe("DETERMINISTIC_DIST_TYPES", () => {
  it("test_deterministicDistTypes_containsExpectedTypes", () => {
    const expected: DistributionType[] = ["sequence", "fixed"];
    expect(DETERMINISTIC_DIST_TYPES).toEqual(expected);
  });
});

// ---------------------------------------------------------------------------
// DIST_PARAMS
// ---------------------------------------------------------------------------
describe("DIST_PARAMS", () => {
  it("test_distParams_uniform_hasLowHigh", () => {
    expect(DIST_PARAMS.uniform).toEqual(["low", "high"]);
  });

  it("test_distParams_hypergeometric_hasThreeParams", () => {
    expect(DIST_PARAMS.hypergeometric).toEqual([
      "populationSize",
      "successCount",
      "sampleSize",
    ]);
  });

  it("test_distParams_fixed_hasValue", () => {
    expect(DIST_PARAMS.fixed).toEqual(["value"]);
  });

  it("test_distParams_sequence_hasStartStep", () => {
    expect(DIST_PARAMS.sequence).toEqual(["start", "step"]);
  });

  it("test_distParams_allTypesHaveAtLeastOneParam", () => {
    for (const type of DIST_TYPES) {
      expect(DIST_PARAMS[type].length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// DIST_PARAM_LABEL_KEYS
// ---------------------------------------------------------------------------
describe("DIST_PARAM_LABEL_KEYS", () => {
  it("test_distParamLabelKeys_allParamsHaveKey", () => {
    const allParams = new Set(Object.values(DIST_PARAMS).flat());
    for (const param of allParams) {
      expect(
        DIST_PARAM_LABEL_KEYS[param],
        `param "${param}" に labelKey がない`,
      ).toBeDefined();
    }
  });
});

// ---------------------------------------------------------------------------
// DIST_PARAM_DEFAULTS
// ---------------------------------------------------------------------------
describe("DIST_PARAM_DEFAULTS", () => {
  it("test_distParamDefaults_normalHasMeanAndStandardDeviation", () => {
    expect(DIST_PARAM_DEFAULTS.normal).toEqual({
      mean: 0,
      standardDeviation: 1,
    });
  });

  it("test_distParamDefaults_binomialHasTrialCountAndSuccessProbability", () => {
    expect(DIST_PARAM_DEFAULTS.binomial).toEqual({
      trialCount: 10,
      successProbability: 0.5,
    });
  });

  it("test_distParamDefaults_sequenceHasStartAndStep", () => {
    expect(DIST_PARAM_DEFAULTS.sequence).toEqual({ start: 1, step: 1 });
  });

  it("test_distParamDefaults_allTypesHaveDefaultsMatchingParams", () => {
    for (const type of DIST_TYPES) {
      const params = DIST_PARAMS[type];
      const defaults = DIST_PARAM_DEFAULTS[type];
      for (const param of params) {
        expect(
          defaults[param],
          `${type}.${param} のデフォルト値がない`,
        ).toBeDefined();
      }
    }
  });
});

// ---------------------------------------------------------------------------
// DIST_PARAM_SCHEMAS — Zod バリデーション境界値テスト
// ---------------------------------------------------------------------------
describe("DIST_PARAM_SCHEMAS", () => {
  const valid = (schemaKey: string, value: string) =>
    DIST_PARAM_SCHEMAS[schemaKey]().safeParse(value).success;

  describe("scaleParameter (gtZeroNum)", () => {
    it("test_scaleParameter_positiveNumber_isValid", () => {
      expect(valid("scaleParameter", "1")).toBe(true);
      expect(valid("scaleParameter", "0.001")).toBe(true);
    });
    it("test_scaleParameter_zero_isInvalid", () => {
      expect(valid("scaleParameter", "0")).toBe(false);
    });
    it("test_scaleParameter_negative_isInvalid", () => {
      expect(valid("scaleParameter", "-1")).toBe(false);
    });
    it("test_scaleParameter_nonNumber_isInvalid", () => {
      expect(valid("scaleParameter", "abc")).toBe(false);
    });
  });

  describe("successProbability (probability: 0 < p <= 1)", () => {
    it("test_successProbability_0dot5_isValid", () => {
      expect(valid("successProbability", "0.5")).toBe(true);
    });
    it("test_successProbability_1_isValid", () => {
      expect(valid("successProbability", "1")).toBe(true);
    });
    it("test_successProbability_0_isInvalid", () => {
      expect(valid("successProbability", "0")).toBe(false);
    });
    it("test_successProbability_greaterThan1_isInvalid", () => {
      expect(valid("successProbability", "1.1")).toBe(false);
    });
    it("test_successProbability_negative_isInvalid", () => {
      expect(valid("successProbability", "-0.1")).toBe(false);
    });
  });

  describe("trialCount (gtZeroInt)", () => {
    it("test_trialCount_positiveInteger_isValid", () => {
      expect(valid("trialCount", "5")).toBe(true);
      expect(valid("trialCount", "1")).toBe(true);
    });
    it("test_trialCount_zero_isInvalid", () => {
      expect(valid("trialCount", "0")).toBe(false);
    });
    it("test_trialCount_float_isInvalid", () => {
      expect(valid("trialCount", "1.5")).toBe(false);
    });
    it("test_trialCount_negative_isInvalid", () => {
      expect(valid("trialCount", "-1")).toBe(false);
    });
  });

  describe("mean / low / high / logMean / value (anyNum)", () => {
    it("test_mean_zero_isValid", () => {
      expect(valid("mean", "0")).toBe(true);
    });
    it("test_low_negative_isValid", () => {
      expect(valid("low", "-100")).toBe(true);
    });
    it("test_value_nonNumber_isInvalid", () => {
      expect(valid("value", "not_a_number")).toBe(false);
    });
  });

  describe("start / step (anyNum)", () => {
    it("test_start_positive_isValid", () => {
      expect(valid("start", "1")).toBe(true);
    });

    it("test_step_negative_isValid", () => {
      expect(valid("step", "-1")).toBe(true);
    });
  });

  describe("rate (gtZeroNum)", () => {
    it("test_rate_positive_isValid", () => {
      expect(valid("rate", "3.5")).toBe(true);
    });
    it("test_rate_zero_isInvalid", () => {
      expect(valid("rate", "0")).toBe(false);
    });
  });

  describe("populationSize / successCount / sampleSize (gtZeroInt)", () => {
    it("test_populationSize_positiveInt_isValid", () => {
      expect(valid("populationSize", "100")).toBe(true);
    });
    it("test_successCount_float_isInvalid", () => {
      expect(valid("successCount", "2.5")).toBe(false);
    });
    it("test_sampleSize_zero_isInvalid", () => {
      expect(valid("sampleSize", "0")).toBe(false);
    });
  });
});

// ---------------------------------------------------------------------------
// buildDistributionFromParams
// ---------------------------------------------------------------------------
describe("buildDistributionFromParams", () => {
  it("test_build_uniform", () => {
    expect(
      buildDistributionFromParams("uniform", { low: 0, high: 10 }),
    ).toEqual({ type: "uniform", low: 0, high: 10 });
  });

  it("test_build_exponential", () => {
    expect(
      buildDistributionFromParams("exponential", { scaleParameter: 2 }),
    ).toEqual({
      type: "exponential",
      scaleParameter: 2,
    });
  });

  it("test_build_normal", () => {
    expect(
      buildDistributionFromParams("normal", {
        mean: 0,
        standardDeviation: 1,
      }),
    ).toEqual({ type: "normal", mean: 0, standardDeviation: 1 });
  });

  it("test_build_gamma", () => {
    expect(
      buildDistributionFromParams("gamma", {
        shapeParameter: 2,
        scaleParameter: 1,
      }),
    ).toEqual({ type: "gamma", shapeParameter: 2, scaleParameter: 1 });
  });

  it("test_build_beta", () => {
    expect(buildDistributionFromParams("beta", { alpha: 2, beta: 2 })).toEqual({
      type: "beta",
      alpha: 2,
      beta: 2,
    });
  });

  it("test_build_weibull", () => {
    expect(
      buildDistributionFromParams("weibull", {
        shapeParameter: 1,
        scaleParameter: 1,
      }),
    ).toEqual({ type: "weibull", shapeParameter: 1, scaleParameter: 1 });
  });

  it("test_build_lognormal", () => {
    expect(
      buildDistributionFromParams("lognormal", {
        logMean: 0,
        logStandardDeviation: 1,
      }),
    ).toEqual({ type: "lognormal", logMean: 0, logStandardDeviation: 1 });
  });

  it("test_build_binomial", () => {
    expect(
      buildDistributionFromParams("binomial", {
        trialCount: 10,
        successProbability: 0.5,
      }),
    ).toEqual({
      type: "binomial",
      trialCount: 10,
      successProbability: 0.5,
    });
  });

  it("test_build_bernoulli", () => {
    expect(
      buildDistributionFromParams("bernoulli", { successProbability: 0.3 }),
    ).toEqual({
      type: "bernoulli",
      successProbability: 0.3,
    });
  });

  it("test_build_poisson", () => {
    expect(buildDistributionFromParams("poisson", { rate: 3 })).toEqual({
      type: "poisson",
      rate: 3,
    });
  });

  it("test_build_geometric", () => {
    expect(
      buildDistributionFromParams("geometric", { successProbability: 0.4 }),
    ).toEqual({
      type: "geometric",
      successProbability: 0.4,
    });
  });

  it("test_build_hypergeometric", () => {
    expect(
      buildDistributionFromParams("hypergeometric", {
        populationSize: 20,
        successCount: 5,
        sampleSize: 10,
      }),
    ).toEqual({
      type: "hypergeometric",
      populationSize: 20,
      successCount: 5,
      sampleSize: 10,
    });
  });

  it("test_build_negative_binomial", () => {
    expect(
      buildDistributionFromParams("negative_binomial", {
        targetSuccessCount: 5,
        successProbability: 0.5,
      }),
    ).toEqual({
      type: "negative_binomial",
      targetSuccessCount: 5,
      successProbability: 0.5,
    });
  });

  it("test_build_fixed", () => {
    expect(buildDistributionFromParams("fixed", { value: 42 })).toEqual({
      type: "fixed",
      value: 42,
    });
  });

  it("test_build_sequence", () => {
    expect(
      buildDistributionFromParams("sequence", { start: 1, step: -1 }),
    ).toEqual({
      type: "sequence",
      start: 1,
      step: -1,
    });
  });
});

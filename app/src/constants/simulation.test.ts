import type { DistributionType } from "@/types/commonTypes";
import { describe, expect, it } from "vitest";
import {
  buildDistributionFromParams,
  CONTINUOUS_DIST_TYPES,
  DISCRETE_DIST_TYPES,
  DIST_PARAM_DEFAULTS,
  DIST_PARAM_LABEL_KEYS,
  DIST_PARAM_SCHEMAS,
  DIST_PARAMS,
  DIST_TYPES,
} from "./simulation";

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

  it("test_distTypes_includesFixed", () => {
    expect(DIST_TYPES).toContain("fixed");
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
  it("test_distParamDefaults_normalHasLocAndScale", () => {
    expect(DIST_PARAM_DEFAULTS.normal).toEqual({ loc: 0, scale: 1 });
  });

  it("test_distParamDefaults_binomialHasNAndP", () => {
    expect(DIST_PARAM_DEFAULTS.binomial).toEqual({ n: 10, p: 0.5 });
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

  describe("scale (gtZeroNum)", () => {
    it("test_scale_positiveNumber_isValid", () => {
      expect(valid("scale", "1")).toBe(true);
      expect(valid("scale", "0.001")).toBe(true);
    });
    it("test_scale_zero_isInvalid", () => {
      expect(valid("scale", "0")).toBe(false);
    });
    it("test_scale_negative_isInvalid", () => {
      expect(valid("scale", "-1")).toBe(false);
    });
    it("test_scale_nonNumber_isInvalid", () => {
      expect(valid("scale", "abc")).toBe(false);
    });
  });

  describe("p (probability: 0 < p <= 1)", () => {
    it("test_p_0dot5_isValid", () => {
      expect(valid("p", "0.5")).toBe(true);
    });
    it("test_p_1_isValid", () => {
      expect(valid("p", "1")).toBe(true);
    });
    it("test_p_0_isInvalid", () => {
      expect(valid("p", "0")).toBe(false);
    });
    it("test_p_greaterThan1_isInvalid", () => {
      expect(valid("p", "1.1")).toBe(false);
    });
    it("test_p_negative_isInvalid", () => {
      expect(valid("p", "-0.1")).toBe(false);
    });
  });

  describe("n (gtZeroInt)", () => {
    it("test_n_positiveInteger_isValid", () => {
      expect(valid("n", "5")).toBe(true);
      expect(valid("n", "1")).toBe(true);
    });
    it("test_n_zero_isInvalid", () => {
      expect(valid("n", "0")).toBe(false);
    });
    it("test_n_float_isInvalid", () => {
      expect(valid("n", "1.5")).toBe(false);
    });
    it("test_n_negative_isInvalid", () => {
      expect(valid("n", "-1")).toBe(false);
    });
  });

  describe("loc / low / high / mean / value (anyNum)", () => {
    it("test_loc_zero_isValid", () => {
      expect(valid("loc", "0")).toBe(true);
    });
    it("test_low_negative_isValid", () => {
      expect(valid("low", "-100")).toBe(true);
    });
    it("test_value_nonNumber_isInvalid", () => {
      expect(valid("value", "not_a_number")).toBe(false);
    });
  });

  describe("lam (gtZeroNum)", () => {
    it("test_lam_positive_isValid", () => {
      expect(valid("lam", "3.5")).toBe(true);
    });
    it("test_lam_zero_isInvalid", () => {
      expect(valid("lam", "0")).toBe(false);
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
    expect(buildDistributionFromParams("exponential", { scale: 2 })).toEqual({
      type: "exponential",
      scale: 2,
    });
  });

  it("test_build_normal", () => {
    expect(buildDistributionFromParams("normal", { loc: 0, scale: 1 })).toEqual(
      { type: "normal", loc: 0, scale: 1 },
    );
  });

  it("test_build_gamma", () => {
    expect(
      buildDistributionFromParams("gamma", { shape: 2, scale: 1 }),
    ).toEqual({ type: "gamma", shape: 2, scale: 1 });
  });

  it("test_build_beta", () => {
    expect(buildDistributionFromParams("beta", { a: 2, b: 2 })).toEqual({
      type: "beta",
      a: 2,
      b: 2,
    });
  });

  it("test_build_weibull", () => {
    expect(buildDistributionFromParams("weibull", { a: 1, scale: 1 })).toEqual({
      type: "weibull",
      a: 1,
      scale: 1,
    });
  });

  it("test_build_lognormal", () => {
    expect(
      buildDistributionFromParams("lognormal", { mean: 0, sigma: 1 }),
    ).toEqual({ type: "lognormal", mean: 0, sigma: 1 });
  });

  it("test_build_binomial", () => {
    expect(buildDistributionFromParams("binomial", { n: 10, p: 0.5 })).toEqual({
      type: "binomial",
      n: 10,
      p: 0.5,
    });
  });

  it("test_build_bernoulli", () => {
    expect(buildDistributionFromParams("bernoulli", { p: 0.3 })).toEqual({
      type: "bernoulli",
      p: 0.3,
    });
  });

  it("test_build_poisson", () => {
    expect(buildDistributionFromParams("poisson", { lam: 3 })).toEqual({
      type: "poisson",
      lam: 3,
    });
  });

  it("test_build_geometric", () => {
    expect(buildDistributionFromParams("geometric", { p: 0.4 })).toEqual({
      type: "geometric",
      p: 0.4,
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
      buildDistributionFromParams("negative_binomial", { n: 5, p: 0.5 }),
    ).toEqual({ type: "negative_binomial", n: 5, p: 0.5 });
  });

  it("test_build_fixed", () => {
    expect(buildDistributionFromParams("fixed", { value: 42 })).toEqual({
      type: "fixed",
      value: 42,
    });
  });
});

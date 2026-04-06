import { describe, expect, it } from "vitest";
import {
  CSV_SEPARATORS,
  DISTRIBUTION_OPTIONS,
  HEADER_MENU_HEIGHT,
  TABLE_TAB_HEIGHT,
} from "@/constants/app";

describe("app constants", () => {
  describe("HEADER_MENU_HEIGHT", () => {
    it("test_headerMenuHeight_is40", () => {
      expect(HEADER_MENU_HEIGHT).toBe(40);
    });
  });

  describe("TABLE_TAB_HEIGHT", () => {
    it("test_tableTabHeight_is40", () => {
      expect(TABLE_TAB_HEIGHT).toBe(40);
    });
  });

  describe("CSV_SEPARATORS", () => {
    it("test_csvSeparators_containsComma", () => {
      expect(CSV_SEPARATORS).toContain(",");
    });
  });

  describe("DISTRIBUTION_OPTIONS", () => {
    it("test_distributionOptions_hasExpectedLength", () => {
      expect(DISTRIBUTION_OPTIONS.length).toBe(13);
    });

    it("test_distributionOptions_eachHasValueLabelParams", () => {
      for (const option of DISTRIBUTION_OPTIONS) {
        expect(option.value).toBeDefined();
        expect(option.label).toBeDefined();
        expect(Array.isArray(option.params)).toBe(true);
      }
    });

    it("test_distributionOptions_normalDistribution", () => {
      const normal = DISTRIBUTION_OPTIONS.find((o) => o.value === "normal");
      expect(normal).toBeDefined();
      expect(normal?.params).toEqual(["loc", "scale"]);
    });

    it("test_distributionOptions_uniformDistribution", () => {
      const uniform = DISTRIBUTION_OPTIONS.find((o) => o.value === "uniform");
      expect(uniform).toBeDefined();
      expect(uniform?.params).toEqual(["low", "high"]);
    });

    it("test_distributionOptions_hypergeometricHasThreeParams", () => {
      const hyper = DISTRIBUTION_OPTIONS.find(
        (o) => o.value === "hypergeometric",
      );
      expect(hyper?.params).toHaveLength(3);
    });
  });
});

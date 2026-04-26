import {
  CSV_SEPARATORS,
  HEADER_MENU_HEIGHT,
  TABLE_TAB_HEIGHT,
} from "@/constants/app";
import { describe, expect, it } from "vitest";

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
});

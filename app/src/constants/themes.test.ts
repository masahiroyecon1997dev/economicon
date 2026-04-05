import { describe, expect, it } from "vitest";
import { THEMES } from "./themes";

describe("THEMES", () => {
  it("test_themes_hasAtLeastOneTheme", () => {
    expect(THEMES.length).toBeGreaterThan(0);
  });

  it("test_themes_eachHasRequiredFields", () => {
    for (const theme of THEMES) {
      expect(theme.id).toBeDefined();
      expect(theme.labelKey).toBeDefined();
      expect(theme.Icon).toBeDefined();
      expect(theme.preview).toBeDefined();
    }
  });

  it("test_themes_eachPreviewHasColorFields", () => {
    const colorFields = [
      "bg",
      "sidebar",
      "border",
      "text",
      "accent",
      "muted",
    ] as const;
    for (const theme of THEMES) {
      for (const field of colorFields) {
        expect(
          theme.preview[field],
          `theme "${theme.id}" の preview.${field} がない`,
        ).toBeDefined();
      }
    }
  });

  it("test_themes_containsLightTheme", () => {
    const light = THEMES.find((t) => t.id === "light");
    expect(light).toBeDefined();
    expect(light?.labelKey).toBe("SettingsDialog.Theme.Light");
  });

  it("test_themes_containsDarkTheme", () => {
    const dark = THEMES.find((t) => t.id === "dark");
    expect(dark).toBeDefined();
    expect(dark?.labelKey).toBe("SettingsDialog.Theme.Dark");
  });

  it("test_themes_allIdsAreUnique", () => {
    const ids = THEMES.map((t) => t.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

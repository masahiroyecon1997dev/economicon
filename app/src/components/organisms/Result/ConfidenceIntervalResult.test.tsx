import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ConfidenceIntervalResultEntry } from "../../../stores/confidenceIntervalResults";
import { ConfidenceIntervalResult } from "./ConfidenceIntervalResult";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------
const makeEntry = (
  overrides: Partial<ConfidenceIntervalResultEntry> = {},
): ConfidenceIntervalResultEntry => ({
  id: "test-id",
  tableName: "sales",
  columnName: "price",
  statistic: { type: "mean", value: 120.5 },
  confidenceInterval: { lower: 115.1234, upper: 126.5678 },
  confidenceLevel: 0.95,
  ...overrides,
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("ConfidenceIntervalResult — 表示テスト", () => {
  describe("ヘッダーセクション", () => {
    it("test_header_showsTableNameAndColumnName", () => {
      render(<ConfidenceIntervalResult result={makeEntry()} />);
      expect(screen.getByText("sales / price")).toBeInTheDocument();
    });

    it("test_header_showsTitleKey", () => {
      render(<ConfidenceIntervalResult result={makeEntry()} />);
      expect(
        screen.getByText("ConfidenceIntervalView.Title"),
      ).toBeInTheDocument();
    });
  });

  describe("結果テーブル", () => {
    it("test_result_showsStatisticTypeKey", () => {
      render(<ConfidenceIntervalResult result={makeEntry()} />);
      expect(
        screen.getByText("ConfidenceIntervalView.StatisticType_mean"),
      ).toBeInTheDocument();
    });

    it("test_result_showsPointEstimateFormatted", () => {
      render(<ConfidenceIntervalResult result={makeEntry()} />);
      // 120.5 → toFixed(4) → "120.5000"
      expect(screen.getByText("120.5000")).toBeInTheDocument();
    });

    it("test_result_showsIntegerPointEstimateWithLocale", () => {
      render(
        <ConfidenceIntervalResult
          result={makeEntry({ statistic: { type: "mean", value: 200 } })}
        />,
      );
      expect(screen.getByText("200")).toBeInTheDocument();
    });

    it("test_result_showsConfidenceLevelAsPercent", () => {
      render(<ConfidenceIntervalResult result={makeEntry()} />);
      expect(screen.getByText("95%")).toBeInTheDocument();
    });

    it("test_result_showsConfidenceLevel99", () => {
      render(
        <ConfidenceIntervalResult
          result={makeEntry({ confidenceLevel: 0.99 })}
        />,
      );
      expect(screen.getByText("99%")).toBeInTheDocument();
    });

    it("test_result_showsLowerBoundFormatted", () => {
      render(<ConfidenceIntervalResult result={makeEntry()} />);
      expect(screen.getByText("115.1234")).toBeInTheDocument();
    });

    it("test_result_showsUpperBoundFormatted", () => {
      render(<ConfidenceIntervalResult result={makeEntry()} />);
      expect(screen.getByText("126.5678")).toBeInTheDocument();
    });

    it("test_result_showsDashForNullValue", () => {
      render(
        <ConfidenceIntervalResult
          result={makeEntry({ statistic: { type: "mean", value: null } })}
        />,
      );
      expect(screen.getByText("—")).toBeInTheDocument();
    });

    it("test_result_hasTestid", () => {
      const { container } = render(
        <ConfidenceIntervalResult result={makeEntry()} />,
      );
      const el = container.querySelector(
        "[data-testid='confidence-interval-result']",
      );
      expect(el).toBeTruthy();
    });
  });

  describe("statisticType が median のとき", () => {
    it("test_result_medianStatisticTypeKey", () => {
      render(
        <ConfidenceIntervalResult
          result={makeEntry({
            statistic: { type: "median", value: 118.0 },
          })}
        />,
      );
      expect(
        screen.getByText("ConfidenceIntervalView.StatisticType_median"),
      ).toBeInTheDocument();
    });
  });
});

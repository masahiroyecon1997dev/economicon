import { getEconomiconAppAPI } from "@/api/endpoints";
import { ConfidenceIntervalResult } from "@/components/organisms/Result/ConfidenceIntervalResult";
import type { ConfidenceIntervalResultEntry } from "@/stores/confidenceIntervalResults";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("@/api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

vi.mock("@/components/organisms/Dialog/OutputResultDialog", () => ({
  OutputResultDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="ci-output-dialog">output dialog</div> : null,
}));

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------
const makeEntry = (
  overrides: Partial<ConfidenceIntervalResultEntry> = {},
): ConfidenceIntervalResultEntry => ({
  resultId: "test-result-id",
  tableName: "sales",
  columnName: "price",
  statistic: { type: "mean", value: 120.5 },
  confidenceInterval: { lower: 115.1234, upper: 126.5678 },
  confidenceLevel: 0.95,
  ...overrides,
});

const mockOutputResult = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    outputResult: mockOutputResult,
  } as never);
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: {
      writeText: vi.fn().mockResolvedValue(undefined),
    },
  });
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

    it("test_result_showsOutputButtons", () => {
      render(<ConfidenceIntervalResult result={makeEntry()} />);
      expect(screen.getByTestId("ci-quick-copy-md-btn")).toBeInTheDocument();
      expect(
        screen.getByTestId("ci-open-output-dialog-btn"),
      ).toBeInTheDocument();
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

  describe("出力操作", () => {
    it("test_output_quickCopy_callsOutputResultWithConfidenceInterval", async () => {
      mockOutputResult.mockResolvedValueOnce({
        code: "OK",
        result: { content: "| Result |", format: "markdown" },
      });
      const user = userEvent.setup();

      render(<ConfidenceIntervalResult result={makeEntry()} />);
      await user.click(screen.getByTestId("ci-quick-copy-md-btn"));

      await waitFor(() => {
        expect(mockOutputResult).toHaveBeenCalledWith(
          expect.objectContaining({
            resultType: "confidence_interval",
            resultIds: ["test-result-id"],
            format: "markdown",
          }),
        );
      });
    });

    it("test_output_dialogButton_opensDialog", async () => {
      const user = userEvent.setup();

      render(<ConfidenceIntervalResult result={makeEntry()} />);
      await user.click(screen.getByTestId("ci-open-output-dialog-btn"));

      expect(screen.getByTestId("ci-output-dialog")).toBeInTheDocument();
    });
  });
});

import { getEconomiconAppAPI } from "@/api/endpoints";
import type { AnalysisResultDetail } from "@/api/model";
import { StatisticalTestResult } from "@/components/organisms/Result/StatisticalTestResult";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

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
    open ? <div data-testid="statistical-test-output-dialog" /> : null,
}));

const mockOutputResult = vi.fn();

const makeDetail = (
  overrides: Partial<AnalysisResultDetail> = {},
): AnalysisResultDetail => ({
  id: "stat-test-result-id",
  name: "t-test（1群） #1",
  description: "",
  tableName: "sales",
  resultType: "statistical_test",
  resultData: {
    statistic: 2.3456,
    pValue: 0.021,
    df: 48,
    confidenceInterval: { lower: 0.11, upper: 1.23 },
    confidenceLevel: 0.95,
    effectSize: 0.44,
  },
  createdAt: "2026-05-05T10:00:00Z",
  modelPath: null,
  modelType: null,
  entityIdColumn: null,
  timeColumn: null,
  summaryText: "statistical_test",
  ...overrides,
});

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

describe("StatisticalTestResult", () => {
  it("t 検定の結果を表示する", () => {
    render(<StatisticalTestResult detail={makeDetail()} />);

    expect(screen.getByText("StatisticalTestResult.Title")).toBeInTheDocument();
    expect(screen.getByText("t-test（1群） #1")).toBeInTheDocument();
    expect(
      screen.getByText("StatisticalTestResult.Type_t-test"),
    ).toBeInTheDocument();
    expect(screen.getByText("2.3456")).toBeInTheDocument();
    expect(screen.getByText("0.0210")).toBeInTheDocument();
    expect(screen.getByText("95%")).toBeInTheDocument();
  });

  it("F 検定では df2 を表示し、信頼区間を出さない", () => {
    render(
      <StatisticalTestResult
        detail={makeDetail({
          name: "f-test（2群） #1",
          resultData: {
            statistic: 4.5678,
            pValue: 0.0123,
            df: 10,
            df2: 18,
            confidenceInterval: null,
            effectSize: 0.32,
          },
        })}
      />,
    );

    expect(
      screen.getByText("StatisticalTestResult.Type_f-test"),
    ).toBeInTheDocument();
    expect(screen.getByText("18")).toBeInTheDocument();
    expect(
      screen.queryByText("StatisticalTestResult.ConfidenceInterval"),
    ).toBeNull();
  });

  it("出力ダイアログを開ける", async () => {
    const user = userEvent.setup();
    render(<StatisticalTestResult detail={makeDetail()} />);

    await user.click(
      screen.getByTestId("statistical-test-open-output-dialog-btn"),
    );

    expect(
      screen.getByTestId("statistical-test-output-dialog"),
    ).toBeInTheDocument();
  });

  it("クイックコピーで statistical_test 出力を呼ぶ", async () => {
    mockOutputResult.mockResolvedValueOnce({
      code: "OK",
      result: { content: "| test |", format: "markdown" },
    });
    const user = userEvent.setup();
    render(<StatisticalTestResult detail={makeDetail()} />);

    await user.click(screen.getByTestId("statistical-test-quick-copy-md-btn"));

    await waitFor(() => {
      expect(mockOutputResult).toHaveBeenCalledWith(
        expect.objectContaining({
          resultType: "statistical_test",
          resultIds: ["stat-test-result-id"],
        }),
      );
    });
  });
});

import type { DistributionPreviewResult } from "@/api/model";
import { DistributionPreview } from "@/components/pages/DistributionPreview";
import { DIST_PARAM_DEFAULTS } from "@/constants/simulation";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const { mockPlotlyReact, mockPlotlyPurge } = vi.hoisted(() => ({
  mockPlotlyReact: vi.fn().mockResolvedValue(undefined),
  mockPlotlyPurge: vi.fn(),
}));

vi.mock("plotly.js-dist-min", () => ({
  react: mockPlotlyReact,
  purge: mockPlotlyPurge,
  newPlot: vi.fn().mockResolvedValue(undefined),
}));

const mockPreview = vi.hoisted(() => ({
  loading: false,
  error: null as string | null,
  result: null as DistributionPreviewResult | null,
}));

vi.mock("@/hooks/useDistributionPreview", () => ({
  useDistributionPreview: () => ({ ...mockPreview }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const buildResult = (isDiscrete = false): DistributionPreviewResult => ({
  x: [0, 0.5, 1],
  yDensity: [0.1, 0.4, 0.1],
  yCumulative: [0.1, 0.5, 1.0],
  isDiscrete,
});

beforeEach(() => {
  vi.clearAllMocks();
  mockPreview.loading = false;
  mockPreview.error = null;
  mockPreview.result = null;
  useWorkspaceTabsStore.setState({ tabs: [], activeTabId: null });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("DistributionPreview", () => {
  describe("初期レンダリング", () => {
    it("test_render_showsContainer", () => {
      render(<DistributionPreview />);
      expect(screen.getByTestId("distribution-preview")).toBeInTheDocument();
    });

    it("test_render_showsContinuousTabActive", () => {
      render(<DistributionPreview />);
      // 連続タブ TabsTrigger が存在する
      expect(
        screen.getByText("DistributionPreview.TabContinuous"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("DistributionPreview.TabDiscrete"),
      ).toBeInTheDocument();
    });

    it("test_render_defaultDistribution_showsNormalParams", () => {
      render(<DistributionPreview />);
      // normal の mean スライダーが表示される
      expect(screen.getByTestId("param-slider-mean")).toBeInTheDocument();
      expect(
        screen.getByTestId("param-slider-standardDeviation"),
      ).toBeInTheDocument();
    });

    it("test_render_defaultParams_showsCorrectValues", () => {
      render(<DistributionPreview />);
      expect(screen.getByTestId("param-value-mean").textContent).toBe("0");
      expect(
        screen.getByTestId("param-value-standardDeviation").textContent,
      ).toBe("1");
    });
  });

  describe("draftValues からの初期化", () => {
    it("test_render_withDraftValues_initializesCorrectly", () => {
      useWorkspaceTabsStore.setState({
        activeTabId: "work:DistributionPreview",
        tabs: [
          {
            id: "work:DistributionPreview",
            kind: "work",
            featureKey: "DistributionPreview",
            title: "分布プレビュー",
            dirty: false,
            draftValues: {
              distributionType: "exponential",
              distributionParams: { scaleParameter: 3 },
            },
            createdAt: Date.now(),
          },
        ],
      });
      render(<DistributionPreview />);
      expect(
        screen.getByTestId("param-slider-scaleParameter"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("param-value-scaleParameter").textContent).toBe(
        "3",
      );
    });

    it("test_render_withDiscreteDraft_activesCescreteTab", () => {
      useWorkspaceTabsStore.setState({
        activeTabId: "work:DistributionPreview",
        tabs: [
          {
            id: "work:DistributionPreview",
            kind: "work",
            featureKey: "DistributionPreview",
            title: "分布プレビュー",
            dirty: false,
            draftValues: {
              distributionType: "binomial",
              distributionParams: { ...DIST_PARAM_DEFAULTS["binomial"] },
            },
            createdAt: Date.now(),
          },
        ],
      });
      render(<DistributionPreview />);
      expect(screen.getByTestId("param-slider-trialCount")).toBeInTheDocument();
      expect(
        screen.getByTestId("param-slider-successProbability"),
      ).toBeInTheDocument();
    });
  });

  describe("分布タイプ切り替え", () => {
    it("test_typeChange_uniform_showsLowHighSliders", () => {
      const { container } = render(<DistributionPreview />);
      // RadioTagGroup は Radix Tabs 内にあるため querySelector で要素を取得
      const uniformRadio = container.querySelector(
        'input[type="radio"][value="uniform"]',
      ) as HTMLInputElement;
      expect(uniformRadio).not.toBeNull();
      fireEvent.click(uniformRadio);
      expect(screen.getByTestId("param-slider-low")).toBeInTheDocument();
      expect(screen.getByTestId("param-slider-high")).toBeInTheDocument();
    });

    it("test_typeChange_resetsParamsToDefaults", () => {
      const { container } = render(<DistributionPreview />);
      const slider = screen.getByTestId("param-slider-mean");
      fireEvent.change(slider, { target: { value: "5" } });
      expect(screen.getByTestId("param-value-mean").textContent).toBe("5");

      const uniformRadio = container.querySelector(
        'input[type="radio"][value="uniform"]',
      ) as HTMLInputElement;
      expect(uniformRadio).not.toBeNull();
      fireEvent.click(uniformRadio);

      const normalRadio = container.querySelector(
        'input[type="radio"][value="normal"]',
      ) as HTMLInputElement;
      expect(normalRadio).not.toBeNull();
      fireEvent.click(normalRadio);
      expect(screen.getByTestId("param-value-mean").textContent).toBe("0");
    });
  });

  describe("カテゴリタブ（連続 / 離散）切り替え", () => {
    it("test_categorySwitch_toDiscrete_showsBinomialRadio", async () => {
      const user = userEvent.setup();
      const { container } = render(<DistributionPreview />);
      const discreteTab = screen.getByText("DistributionPreview.TabDiscrete");
      await user.click(discreteTab);
      // 離散タブに切り替え後、binomial のラジオが存在する
      await waitFor(() => {
        const binomialRadio = container.querySelector(
          'input[type="radio"][value="binomial"]',
        );
        expect(binomialRadio).not.toBeNull();
      });
    });
  });

  describe("スライダー操作", () => {
    it("test_slider_mean_updatesDisplayValue", () => {
      render(<DistributionPreview />);
      const slider = screen.getByTestId("param-slider-mean");
      fireEvent.change(slider, { target: { value: "3.5" } });
      expect(screen.getByTestId("param-value-mean").textContent).toBe("3.5");
    });

    it("test_slider_standardDeviation_updatesDisplayValue", () => {
      render(<DistributionPreview />);
      const slider = screen.getByTestId("param-slider-standardDeviation");
      fireEvent.change(slider, { target: { value: "2.5" } });
      expect(
        screen.getByTestId("param-value-standardDeviation").textContent,
      ).toBe("2.5");
    });
  });

  describe("ローディング状態", () => {
    it("test_loading_showsSpinner", () => {
      mockPreview.loading = true;
      render(<DistributionPreview />);
      expect(
        screen.getByText("DistributionPreview.Loading"),
      ).toBeInTheDocument();
    });

    it("test_loading_false_noSpinner", () => {
      mockPreview.loading = false;
      render(<DistributionPreview />);
      expect(
        screen.queryByText("DistributionPreview.Loading"),
      ).not.toBeInTheDocument();
    });
  });

  describe("エラー状態", () => {
    it("test_error_showsErrorAlert", () => {
      mockPreview.error = "API エラーが発生しました";
      render(<DistributionPreview />);
      expect(screen.getByText("API エラーが発生しました")).toBeInTheDocument();
    });

    it("test_error_withLoading_hidesErrorAlert", () => {
      mockPreview.error = "エラー";
      mockPreview.loading = true;
      render(<DistributionPreview />);
      expect(screen.queryByText("エラー")).not.toBeInTheDocument();
    });
  });

  describe("結果表示", () => {
    it("test_result_continuous_callsPlotlyReact", async () => {
      mockPreview.result = buildResult(false);
      render(<DistributionPreview />);
      await waitFor(() => {
        expect(mockPlotlyReact).toHaveBeenCalledOnce();
      });
    });

    it("test_result_discrete_callsPlotlyReact", async () => {
      mockPreview.result = buildResult(true);
      render(<DistributionPreview />);
      await waitFor(() => {
        expect(mockPlotlyReact).toHaveBeenCalledOnce();
      });
    });

    it("test_result_plotDivVisible", () => {
      mockPreview.result = buildResult();
      render(<DistributionPreview />);
      const div = screen.getByTestId("distribution-preview-plot");
      expect(div.className).not.toMatch(/hidden/);
    });

    it("test_noResult_plotDivHidden", () => {
      mockPreview.result = null;
      render(<DistributionPreview />);
      const div = screen.getByTestId("distribution-preview-plot");
      expect(div.className).toMatch(/hidden/);
    });
  });

  describe("PDF/PMF vs CDF/CMF タブ", () => {
    it("test_densityTab_isDefault", () => {
      render(<DistributionPreview />);
      expect(
        screen.getByText("DistributionPreview.TabPdfPmf"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("DistributionPreview.TabCdfCmf"),
      ).toBeInTheDocument();
    });

    it("test_switchToCumulative_triggersRerender", async () => {
      const user = userEvent.setup();
      mockPreview.result = buildResult();
      render(<DistributionPreview />);
      await waitFor(() => expect(mockPlotlyReact).toHaveBeenCalled());
      const callsBefore = mockPlotlyReact.mock.calls.length;

      await user.click(screen.getByText("DistributionPreview.TabCdfCmf"));
      await waitFor(() => {
        expect(mockPlotlyReact.mock.calls.length).toBeGreaterThan(callsBefore);
      });
    });
  });
});

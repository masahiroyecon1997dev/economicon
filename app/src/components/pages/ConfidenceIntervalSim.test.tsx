/**
 * ConfidenceIntervalSim コンポーネントのテスト
 *
 * - 初期値で hook が呼ばれること
 * - loading 時も PlotPanel がレンダリングされること
 * - CI タイプ切り替えで表示パラメータが変わること
 */
import type { ConfidenceIntervalSimRequestBody } from "@/api/model";
import { ConfidenceIntervalSim } from "@/components/pages/ConfidenceIntervalSim";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const { mockUseConfidenceIntervalSim } = vi.hoisted(() => ({
  mockUseConfidenceIntervalSim: vi.fn(
    (_params: ConfidenceIntervalSimRequestBody) => ({
      loading: false,
      error: null as string | null,
      result: null,
    }),
  ),
}));

vi.mock("@/hooks/useConfidenceIntervalSim", () => ({
  useConfidenceIntervalSim: mockUseConfidenceIntervalSim,
}));

vi.mock("plotly.js-dist-min", () => ({
  react: vi.fn().mockResolvedValue(undefined),
  purge: vi.fn(),
}));

beforeEach(() => {
  mockUseConfidenceIntervalSim.mockClear();
  mockUseConfidenceIntervalSim.mockImplementation(
    (_params: ConfidenceIntervalSimRequestBody) => ({
      loading: false,
      error: null as string | null,
      result: null,
    }),
  );
});

describe("ConfidenceIntervalSim", () => {
  describe("初期レンダリング", () => {
    it("test_render_showsContainer: confidence-interval-sim コンテナが表示される", () => {
      render(<ConfidenceIntervalSim />);
      expect(screen.getByTestId("confidence-interval-sim")).toBeInTheDocument();
    });

    it("test_render_showsCIBarArea: CI 横棒グラフエリアが表示される", () => {
      render(<ConfidenceIntervalSim />);
      expect(screen.getByTestId("ci-bar-area")).toBeInTheDocument();
    });

    it("test_render_showsCILineArea: カバレッジ折れ線エリアが表示される", () => {
      render(<ConfidenceIntervalSim />);
      expect(screen.getByTestId("ci-line-area")).toBeInTheDocument();
    });

    it("test_render_showsTrialsSlider: 試行回数スライダーが表示される", () => {
      render(<ConfidenceIntervalSim />);
      expect(screen.getByTestId("trials-slider")).toBeInTheDocument();
    });

    it("test_render_showsSampleSizeSlider: サンプルサイズスライダーが表示される", () => {
      render(<ConfidenceIntervalSim />);
      expect(screen.getByTestId("sample-size-slider")).toBeInTheDocument();
    });
  });

  describe("hook 呼び出し", () => {
    it("test_hook_calledWithDefaultParams: 初期 params で hook が呼ばれる", () => {
      render(<ConfidenceIntervalSim />);

      expect(mockUseConfidenceIntervalSim).toHaveBeenCalledWith(
        expect.objectContaining({
          ciType: "mean",
          trials: 100,
          sampleSize: 30,
          confidenceLevel: 0.95,
          trueMean: 0.0,
          trueVariance: 1.0,
        }),
      );
    });

    it("test_hook_loading_showsBarArea: loading=true 時も CI バーエリアがレンダリングされる", () => {
      mockUseConfidenceIntervalSim.mockReturnValue({
        loading: true,
        error: null,
        result: null,
      });

      render(<ConfidenceIntervalSim />);

      expect(screen.getByTestId("ci-bar-area")).toBeInTheDocument();
    });
  });

  describe("CI タイプ切り替え", () => {
    it("test_ciType_mean_showsTrueMeanSlider: mean タブで trueMean スライダーが表示される", () => {
      render(<ConfidenceIntervalSim />);
      // デフォルトは mean タブ
      expect(screen.getByTestId("true-mean-slider")).toBeInTheDocument();
    });

    it("test_ciType_variance_showsTrueVarianceSlider: variance タブに切り替えると trueVariance スライダーが表示される", async () => {
      const user = userEvent.setup();
      render(<ConfidenceIntervalSim />);

      const varianceTab = screen.getByText("ConfidenceIntervalSim.TabVariance");
      await user.click(varianceTab);

      expect(screen.getByTestId("true-variance-slider")).toBeInTheDocument();
    });

    it("test_ciType_variance_hookCalledWithVariance: variance タブ切り替え後 hook が ciType='variance' で呼ばれる", async () => {
      const user = userEvent.setup();
      render(<ConfidenceIntervalSim />);
      mockUseConfidenceIntervalSim.mockClear();

      await user.click(screen.getByText("ConfidenceIntervalSim.TabVariance"));

      expect(mockUseConfidenceIntervalSim).toHaveBeenCalledWith(
        expect.objectContaining({ ciType: "variance" }),
      );
    });
  });

  describe("カウンター表示", () => {
    it("test_counterLabel_formattedCorrectly: result ありの場合 counterLabel が k/M (xx.x%) 形式で表示される", () => {
      mockUseConfidenceIntervalSim.mockReturnValue({
        loading: false,
        error: null,
        result: {
          trueValue: 0.0,
          confidenceLevel: 0.95,
          intervals: [
            { lower: -0.3, upper: 0.4, containsTrue: true },
            { lower: 0.1, upper: 0.8, containsTrue: false },
          ],
        },
      });

      render(<ConfidenceIntervalSim />);

      // frame=0, totalFrames=2, intervals[0].containsTrue=true → coverage=100.0%
      expect(screen.getByTestId("animation-counter")).toHaveTextContent(
        "1/2 (100.0%)",
      );
    });

    it("test_counterLabel_undefined_whenNoResult: result なしではデフォルト表示（0 / 0）になり % 表示はない", () => {
      render(<ConfidenceIntervalSim />);
      // result=null のとき counterLabel=undefined → AnimationControls は "0 / 0" を表示
      const counter = screen.getByTestId("animation-counter");
      expect(counter).toHaveTextContent("0 / 0");
      expect(counter).not.toHaveTextContent("%");
    });
  });
});

/**
 * Unbiasedness コンポーネントのテスト
 *
 * - 初期値で hook が呼ばれること
 * - loading 時も PlotPanel がレンダリングされること
 * - ヒストグラムと折れ線の両エリアが存在すること
 */
import type { UnbiasednessRequestBody } from "@/api/model";
import { Unbiasedness } from "@/components/pages/Unbiasedness";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const { mockUseUnbiasedness } = vi.hoisted(() => ({
  mockUseUnbiasedness: vi.fn((_params: UnbiasednessRequestBody) => ({
    loading: false,
    error: null as string | null,
    result: null,
  })),
}));

vi.mock("@/hooks/useUnbiasedness", () => ({
  useUnbiasedness: mockUseUnbiasedness,
}));

vi.mock("plotly.js-dist-min", () => ({
  react: vi.fn().mockResolvedValue(undefined),
  purge: vi.fn(),
}));

beforeEach(() => {
  mockUseUnbiasedness.mockClear();
  mockUseUnbiasedness.mockImplementation(
    (_params: UnbiasednessRequestBody) => ({
      loading: false,
      error: null as string | null,
      result: null,
    }),
  );
});

describe("Unbiasedness", () => {
  describe("初期レンダリング", () => {
    it("test_render_showsContainer: unbiasedness コンテナが表示される", () => {
      render(<Unbiasedness />);
      expect(screen.getByTestId("unbiasedness")).toBeInTheDocument();
    });

    it("test_render_showsHistogramArea: ヒストグラムエリアが表示される", () => {
      render(<Unbiasedness />);
      expect(screen.getByTestId("unbiasedness-hist-area")).toBeInTheDocument();
    });

    it("test_render_showsLineArea: 累積平均折れ線エリアが表示される", () => {
      render(<Unbiasedness />);
      expect(screen.getByTestId("unbiasedness-line-area")).toBeInTheDocument();
    });

    it("test_render_showsNumTrialsSlider: 試行回数スライダーが表示される", () => {
      render(<Unbiasedness />);
      expect(screen.getByTestId("num-trials-slider")).toBeInTheDocument();
    });

    it("test_render_showsSampleSizeSlider: サンプルサイズスライダーが表示される", () => {
      render(<Unbiasedness />);
      expect(screen.getByTestId("sample-size-slider")).toBeInTheDocument();
    });
  });

  describe("hook 呼び出し", () => {
    it("test_hook_calledWithDefaultParams: 初期 params で hook が呼ばれる", () => {
      render(<Unbiasedness />);

      expect(mockUseUnbiasedness).toHaveBeenCalledWith(
        expect.objectContaining({
          numTrials: 200,
          sampleSize: 50,
          trueBeta: 1.0,
          errorVariance: 1.0,
        }),
      );
    });

    it("test_hook_loading_showsPlotArea: loading=true 時も hist エリアがレンダリングされる", () => {
      mockUseUnbiasedness.mockReturnValue({
        loading: true,
        error: null,
        result: null,
      });

      render(<Unbiasedness />);

      expect(screen.getByTestId("unbiasedness-hist-area")).toBeInTheDocument();
    });
  });

  describe("AnimationControls", () => {
    it("test_animationControls_present: AnimationControls が表示される", () => {
      render(<Unbiasedness />);
      expect(screen.getByTestId("animation-play-btn")).toBeInTheDocument();
    });

    it("test_animationControls_canPlay_false_whenNoResult: result なしでは再生ボタンが disabled", () => {
      render(<Unbiasedness />);
      expect(screen.getByTestId("animation-play-btn")).toBeDisabled();
    });
  });
});
